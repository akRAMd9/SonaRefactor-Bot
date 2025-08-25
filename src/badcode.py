def insecure_eval(user_input):
    # This is a classic SonarQube red flag
    return eval(user_input)

def bad_default_arg(x=[]):  # mutable default arg
    x.append(1)
    return x
