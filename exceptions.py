class EnvironmentVariablesException(Exception):
    def __init__(self, *args):
        if args:
            self.message = f'Переменная окружения {args[0]} не должна быть пустой'
        else:
            self.message = 'Переменная окружения не должна быть пустой'

    def __str__(self):
        return self.message
