from nicegui import ui

import main

main.create()

ui.run(just_build='pyscript', storage_secret='a_random_and_long_secret_string_for_testing') 