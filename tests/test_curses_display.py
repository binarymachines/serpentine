
import curses
from cli import *



class TestDisplayClient:
      def __init__(self):
            pass

      def run(self, screen, **kwargs):
            Notice("Hello World from curses!!").show(screen)
            #prompt = TextPrompt("Get out?")
            myMenu = Menu(['a', 'b', 'c'])
            prompt = MenuPrompt(myMenu, 'Select a letter.')
            option = prompt.show(screen)
            


def main():
    cd = CursesDisplay(TestDisplayClient)
    cd.open()


if __name__=='__main__':
      main()
