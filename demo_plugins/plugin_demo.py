"""
    Written by TotallyNotK0
    Last updated: March 20, 2025

    This is an example plugin. It was created to test the implementation of
    plugin support.

    Permission is granted to repurpose this script as a foundation to build your
    own, with or without credit.
"""

from PyQt5.QtWidgets import QAction, QMessageBox

def register_plugin(app_context):
    main_window = app_context["main_window"]
    menu_bar = main_window.menuBar()

    demo_plugin_menu = menu_bar.findChild(type(menu_bar), "My Plugin")
    if not demo_plugin_menu:
        demo_plugin_menu = menu_bar.addMenu("My Plugin")
        demo_plugin_menu.setObjectName("My Plugin")

    test_action = QAction("Plugin Demo", main_window)

    def show_message():
        QMessageBox.information(
            main_window,
            "Plugin Demo",
            "Hello, World from Construct Plugin!"
        )

    test_action.triggered.connect(show_message)
    demo_plugin_menu.addAction(test_action)
