def greeting_deco(org_f):
    def wrapper(*args, **kwargs):
        return "Hi {}".format(org_f(*args, **kwargs))

    return wrapper


def random_id_deco(org_f):
    import random
    def wrapper(*args, **kwargs):
        return "{} your id is {}".format(org_f(*args, **kwargs),
                                         "".join(random.choices([str(n) for n in range(10)], k=8)))

    return wrapper


# and you want to apply both decorator to my_name function

def my_name(name):
    return name


# We can apply both decorators as below
# my_name = random_id_deco(greeting_deco(my_name))
# and it the exactly the same when we place them above our function that we need to apply the both decorators to it

@random_id_deco
@greeting_deco
def my_name(name):
    return name


print(my_name.__name__)


# The output will be wrapper  and it is the name of the returned function from our greeting_deco
# and that will cause a conflict if we apply it to another function lets say we have a student_name function that it is the same as  our my_name function

@random_id_deco
@greeting_deco
def student_name(name):
    return name


# and if you check if the name of returned function is the same here it will cause conflict in our namespace
print(my_name.__name__ == student_name.__name__)  # it will be True

# and to solve it we can just add wraps decorator from funtools module that will track each function name so it will solve it to us so try to check the both functions name after adding wraps to our both decorators

print(my_name.__name__ == student_name.__name__)  # it will be False