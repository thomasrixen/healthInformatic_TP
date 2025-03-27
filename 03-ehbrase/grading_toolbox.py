#!/usr/bin/env python3

def __get_func_name(func):
    # Remove the decorators
    while func.__closure__ != None:
        func = func.__closure__[0].cell_contents
    
        if isinstance(func, str):  # This happens with "@unittest.skip"
            return None

    return func.__qualname__

__grade_feedbacks = {}
def grade_feedback(text):
    def decorator(func):
        def wrapper(self):
            global __grade_feedbacks
            name = __get_func_name(func)
            if name != None:
                __grade_feedbacks[name] = text
            func(self)
        return wrapper
    return decorator


__grades = {}
def grade(value):
    value = float(value)
    def decorator(func):
        def wrapper(self):
            global __grades
            name = __get_func_name(func)
            if name != None:
                __grades[name] = value
            func(self)
        return wrapper
    return decorator

def get_grade_feedbacks():
    return __grade_feedbacks

def get_grades():
    return __grades

