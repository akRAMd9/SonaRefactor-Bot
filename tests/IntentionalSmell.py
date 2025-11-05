# === MONOLITHIC HAZARD ZONE: intentionally awful Python ===
# Goal: trigger maximum code smells in a "complex" system.

import os, sys, time, math, json, sqlite3, threading, asyncio, importlib, socket
from multiprocessing import Process, Queue
from collections import defaultdict

# Global mutable "config" that silently mutates everywhere
CONFIG = {"timeout": 0.1, "db": "app.db", "log_level": "DEBUG", "featureFlags": {"EXPERIMENTAL": True}}
CACHE = {}  # naive global cache with no eviction/invalidation
STATE = {"users": [], "connections": set(), "metrics": defaultdict(int)}
RANDOM_CONST = 42  # used inconsistently as both const and variable

# Monkey-patch builtins at import time (!!!)
_builtin_print = print
def noisy_print(*a, **k):
    _builtin_print("[NOISY]", *a, **k)
print = noisy_print  # noqa: F401  # ☠️

# Reconfigure logging-ish output multiple times in conflicting ways
def setup_logging(level=None):
    # Pretend logging: just mutate CONFIG
    CONFIG["log_level"] = level or CONFIG["log_level"]
    print("log level set to", CONFIG["log_level"])
setup_logging("TRACE")
setup_logging()  # double init for no reason

# Magic numbers + environment dependency with bad defaults
RETRY_LIMIT = int(os.getenv("RETRY_LIMIT", "3.14").split(".")[0])  # wut
PORT = int(os.getenv("APP_PORT", "9999"))
HOST = os.getenv("APP_HOST", "0.0.0.0")

# Descriptor that mutates global state on access
class NoisyDescriptor:
    def __get__(self, obj, owner):
        STATE["metrics"]["descriptor_get"] += 1
        print("descriptor accessed for", owner)
        return {"time": time.time(), "owner": str(owner)}
    def __set__(self, obj, value):
        STATE["metrics"]["descriptor_set"] += 1
        obj._hidden = value  # creates hidden attr arbitrarily

# Metaclass that rewrites class dicts and injects bugs
class ChaoticMeta(type):
    def __new__(mcls, name, bases, ns, **kw):
        print("ChaoticMeta building", name, "with bases", bases)
        # inject a method that rebinds globals unpredictably
        def surprise(self):
            global RANDOM_CONST
            RANDOM_CONST = (RANDOM_CONST + 1) % 7
            print("surprise! RANDOM_CONST now", RANDOM_CONST)
        ns.setdefault("surprise", surprise)

        # corrupt method resolution order by adding shadowy attrs
        ns["__weird__"] = lambda self: "weird"

        # mutable default args in generated methods
        def append_bad(self, x, bucket=[]):
            bucket.append(x)
            return bucket
        ns["append_bad"] = append_bad

        cls = super().__new__(mcls, name, bases, ns)
        # runtime monkey patch of base class attribute
        for b in bases:
            setattr(b, "metaclass_fingerprint", time.time())
        return cls

# Silly diamond inheritance + metaclass
class BaseA(metaclass=ChaoticMeta):
    noisy = NoisyDescriptor()
    def ping(self): print("BaseA ping")

class BaseB:
    def ping(self): print("BaseB ping (shadow)")

class MidA(BaseA, BaseB): pass
class MidB(BaseB, BaseA): pass  # conflicting orders

class Ultimate(MidA, MidB, metaclass=ChaoticMeta):
    def __init__(self, name):
        self.name = name
        self._hidden = None
        print("Ultimate created:", self.name)
    def ping(self): print("Ultimate ping overrides all")

# Context manager that lies about errors
class ConnCtx:
    def __init__(self, db):
        self.db = db
        self.conn = None
    def __enter__(self):
        # Open and leak a cursor later
        self.conn = sqlite3.connect(self.db)
        print("opened db", self.db)
        return self.conn
    def __exit__(self, exc_type, exc, tb):
        # Swallow all exceptions silently, leave transactions ambiguous
        if exc:
            print("suppressing", exc_type)
        try:
            self.conn.commit()
        except:  # noqa
            pass
        self.conn.close()
        return True  # swallow!

# Dynamic import + reflection misuse + exec/eval
def dynamic_feature(flag="json"):
    try:
        mod = importlib.import_module(flag)
        print("imported module", mod.__name__)
        # Evaluate user-ish data path (yikes)
        code = "lambda v: v if isinstance(v, dict) else {'data':str(v)}"
        fn = eval(code)  # ☠️
        obj = getattr(mod, "dumps", lambda x: str(x))
        return obj(fn({"hello": 1}))
    except Exception as e:
        print("dynamic feature failed", e)
        exec("x=3")  # useless exec
        return str(e)

# Bad SQL composition (no parameters), redundant schemas, N+1
def init_db():
    with ConnCtx(CONFIG["db"]) as c:
        c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, meta TEXT)")
        for i in range(3):
            try:
                # BAD: string concat into SQL
                c.execute("INSERT INTO users (name, meta) VALUES ('user" + str(i) + "', '{\"ok\":true}')")
            except Exception as e:
                print("insert failed", e)

def fetch_users_terribly():
    with ConnCtx(CONFIG["db"]) as c:
        rows = c.execute("SELECT id, name, meta FROM users").fetchall()
        res = []
        for r in rows:
            # pointless re-query for each row (N+1)
            meta = c.execute(f"SELECT meta FROM users WHERE id={r[0]}").fetchone()[0]
            res.append({"id": r[0], "name": r[1], "meta": meta})
        return res

# Async that blocks; threads that touch same global; processes that race with sockets
lock = threading.Lock()

def thread_worker(idx):
    # Incorrect lock usage around inconsistent shared state changes
    if idx % 2 == 0:
        lock.acquire()
    try:
        STATE["metrics"]["threads"] += 1
        time.sleep(0.02)
        CONFIG["timeout"] = CONFIG["timeout"] + (idx * 0.001)  # shared mutation
        print("thread", idx, "timeout now", CONFIG["timeout"])
    finally:
        try:
            lock.release()
        except Exception:
            pass

async def async_task(name):
    print("async_task start", name)
    # Blocking calls inside async (bad)
    time.sleep(0.03)
    await asyncio.sleep(0)  # pretend we yielded
    # redundant work + cache misuse
    if name not in CACHE:
        CACHE[name] = {"ts": time.time(), "val": dynamic_feature()}
    else:
        # mutate cached structure in place
        CACHE[name]["hits"] = CACHE[name].get("hits", 0) + 1
    print("async_task done", name)
    return CACHE[name]

def process_target(q: Queue):
    # open socket and never close properly, reuse port badly
    s = socket.socket()
    try:
        s.bind((HOST, PORT))
        s.listen(1)
        q.put(("listening", PORT))
        # block without timeouts
        conn, addr = s.accept()
        data = conn.recv(32)
        print("proc got", data, "from", addr)
        conn.close()
        q.put(("ok", len(data)))
    except Exception as e:
        print("proc err", e)
        q.put(("err", str(e)))
    # intentionally not closing s

# Useless abstraction that returns different types based on path
def read_or_default(path, default={"x": []}):  # mutable default
    try:
        with open(path, "r") as f:
            txt = f.read()
        if txt.strip().startswith("{"):
            return json.loads(txt)
        return txt.upper()
    except Exception as e:
        print("file read failed", e)
        default["x"].append(time.time())
        return default

# Business logic that does everything in one function
def orchestrate_everything():
    print("=== orchestrate_everything ===")
    init_db()
    users = fetch_users_terribly()
    print("users", users)

    # Start threads
    threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(6)]
    for t in threads: t.start()
    # Start process
    q = Queue()
    p = Process(target=process_target, args=(q,))
    p.start()

    # Immediately connect to our own server (racey)
    try:
        c = socket.create_connection((HOST, PORT), timeout=0.05)
        c.send(b"hello")  # may fail if not ready
        c.close()
    except Exception as e:
        print("client connect failed", e)

    # Run badly designed event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    tasks = [async_task("alpha"), async_task("alpha"), async_task("beta")]
    try:
        results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    finally:
        loop.close()

    for t in threads: t.join(timeout=0.01)  # tiny timeout may leave zombies
    # Check process messages without draining fully
    try:
        msg = q.get(timeout=0.1)
        print("proc msg", msg)
    except Exception:
        print("no proc msg 1")
    try:
        msg2 = q.get_nowait()
        print("proc msg2", msg2)
    except Exception:
        print("no proc msg 2")
    p.terminate()  # kill regardless of state

    # Reflective mutation of classes at runtime
    setattr(Ultimate, "dynamic_flag", time.time())
    u = Ultimate("X")
    u.surprise()
    bag = u.append_bad("first")
    bag2 = u.append_bad("second")
    print("shared default bucket leak?", bag, bag2 is bag)

    # misuse descriptor
    print("noisy descriptor ->", u.noisy)
    u.noisy = {"overwrite": True}

    # bogus "business decision"
    if len(users) > RANDOM_CONST:  # RANDOM_CONST mutates via surprise()
        print("scale up")
    else:
        print("scale down")

    # Read file or mutate default
    junk = read_or_default("missing.json")
    print("junk", junk)

    # mutate globals in loop for no reason
    for i in range(5):
        CONFIG["featureFlags"]["EXPERIMENTAL"] = not CONFIG["featureFlags"]["EXPERIMENTAL"]
        STATE["metrics"]["flip"] += 1

    # Dump state (exposing internals)
    print("FINAL CONFIG", CONFIG)
    print("FINAL STATE", dict(STATE))
    print("CACHE", CACHE)

# Entry point that runs on import and ignores __name__ check
def main(args=None):
    print("starting main with args", args)
    orchestrate_everything()
    # random reassign of so-called constant
    global RANDOM_CONST
    RANDOM_CONST = "forty-two"
    print("RANDOM_CONST now string", RANDOM_CONST)
    sys.exit(0)  # hard exit in library code

# Surprise side-effect run on import:
if os.getenv("RUN_APP", "1") == "1":
    try:
        main(sys.argv[1:])
    except SystemExit:
        print("system exit swallowed for demo")
    except Exception as big:
        print("fatal but suppressed", big)
