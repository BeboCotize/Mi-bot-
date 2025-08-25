from telegram.ext import CommandHandler

def custom_commands(application):
    # Aquí registramos los comandos con prefijos .!*?
    prefixes = [".", "!", "*", "?"]

    def prefixed_command(prefix, command, handler):
        for p in prefixes:
            application.add_handler(CommandHandler(f"{p}{command}", handler))

    # Ejemplo de comandos
    from generador import generar_cc, bin_info
    from registro import registrar_usuario

    prefixed_command(".", "gen", generar_cc)
    prefixed_command(".", "bin", bin_info)
    prefixed_command(".", "registrar", registrar_usuario) 