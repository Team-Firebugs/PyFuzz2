__author__ = 'susperius'

class Window:

    @staticmethod
    def setTimeout(function, timeout):
        return "window.setTimeout(function () { " + function + " }, " + str(timeout) + ");"
