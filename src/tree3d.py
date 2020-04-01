import specialized_gui

if __name__ == "__main__":
    app = specialized_gui.MyApp(redirect=False)  # do not redirect stdout to the gui
    app.MainLoop()  # render gui continuously