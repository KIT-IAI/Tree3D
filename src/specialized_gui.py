# -*- coding: utf-8 -*-

# import wxPython classes
import wx

# import project classes
import default_gui


class MainTableFrame(default_gui.MainWindow):

    def __init__(self, parent):
        default_gui.MainWindow.__init__(self, parent)

    def on_menu_open(self, event):
        print("selected open")


# wxPython App erzeugen
class MyApp(wx.App):
    def OnInit(self):
        # create instance of MainTableFrame
        self.frame = MainTableFrame(None)

        self.SetTopWindow(self.frame)
        self.frame.Show(True)
        return True


if __name__ == "__main__":
    app = MyApp(redirect=False)  # do not redirect stdout to the gui
    app.MainLoop()  # render gui continuously
