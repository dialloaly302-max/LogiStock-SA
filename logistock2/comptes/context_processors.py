from .menu import menu_pour


def menu(request):
    return {"menu": menu_pour(request.user)}