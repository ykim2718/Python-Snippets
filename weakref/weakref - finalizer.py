"""
y, 2020.4.9; 2023.12.5
weakref - finalizer, py
https://docs.python.org/3.6/library/weakref.html#finalizer-objects
"""

import weakref


class Object:
    pass


if False:
    kenny = Object()
    weakref.finalize(kenny, print, "You killed Kenny!")
    del kenny

else:
    def func():
        kenny = Object()
        weakref.finalize(kenny, print, "You killed Kenny!")
        return kenny
    kenny = func()

print('end...')
