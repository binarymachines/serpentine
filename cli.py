#!/usr/bin/python

import os, sys
import curses, traceback
import curses.wrapper
from StringIO import StringIO

class UserInputError: pass

class MenuError: pass

class MenuInputError: pass


class Menu:
    def __init__(self, valuesArray): 
        self.values = valuesArray

    def __str__(self):
        index = 1
        entries = []
        for item in self.values:
            entries.append('[%s]\t%s' % (index, item))
            index += 1
        return '\n'.join(entries)

    def values(self):
        return self.values


class MenuPrompt:
    def __init__(self, menu, prompt):
            self.menu = menu
            self.defaultMsg = ["(Hit the * key to exit)"]
            self.defaultMsg.insert(0, prompt)
            self.selectedIndex = -1
            self.selection = ''
            self.escaped = False
            self.reply = ''
               
    def show(self, screen):
            screen.clear()
            buffer = StringIO()
            buffer.write('%s\n%s\n:' % (self.menu, self.defaultMsg))
            contents = buffer.getvalue()
            bufferLineArray = contents.split('\n')
            bufferLineCount = len(bufferLineArray)
            while True:          
                cursorRow = bufferLineCount - 1
                cursorColumn = len(bufferLineArray[bufferLineCount-1])

                screen.addstr(buffer.getvalue())
                screen.move(cursorRow, cursorColumn)
                self.reply = screen.getstr(cursorRow, cursorColumn)

                if self.reply == '*' :                        
                        self.escaped = True
                        break            
                try:   
                        self.selectedIndex = int(self.reply)
                        if self.selectedIndex < 1: 
                            raise IndexError
                        self.selection = self.menu.values[self.selectedIndex - 1]
                        break
                except IndexError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()     
                except ValueError:
                        screen.addstr('\nYour choice must be a numeric index from the menu. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                except MenuInputError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                
            buffer.close()
            return self.selection

class MultipleChoiceMenuPrompt:
    def __init__(self, menu, prompt):
        self.menu = menu
        
        self.defaultMsg = ["Type * to exit.", "Type # to see the items you've selected.", "Type c to clear your selections."]
        self.defaultMsg.insert(0, prompt)
        self.selections = []
        self.escaped = False
        self.selectedIndex = -1
        self.choice = ''

    def show(self, screen):
        screen.clear()

        buffer = StringIO()
        buffer.write('%s\n%s\n:' % (self.menu, '\n'.join(self.defaultMsg)))
        contents = buffer.getvalue()
        bufferLineArray = contents.split('\n')
        bufferLineCount = len(bufferLineArray)

        while True:

            cursorRow = bufferLineCount - 1
            cursorColumn = len(bufferLineArray[bufferLineCount-1])

            screen.addstr(buffer.getvalue())
            screen.move(cursorRow, cursorColumn)
            self.reply = screen.getstr(cursorRow, cursorColumn)

            if self.reply == '*':
                #print 'Exiting menu.'
                self.escaped = True
                break
            if self.reply == '#':
                screen.addstr('You have selected: ' + ', '.join(self.selections) + '\nHit any key to continue.')
                screen.getch()
                screen.clear()
                continue
            elif self.reply == 'c':
                self.selections = []
                screen.getch()
                screen.clear()
                continue
            elif ',' in self.reply:
                newSelections = [item.strip() for item in self.reply.split(',')]
                for selectedIndex in newSelections:
                    try:
                        selectedIndex = int(self.reply)
                        if selectedIndex < 1 : raise IndexError
                        self.selections.append(self.menu.values[selectedIndex - 1])
                    except IndexError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                        break
                     except ValueError:
                        screen.addstr('\nYour choice must be a numeric index from the menu. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                        break
                     except errors.MenuInputError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                        break

                screen.addstr('You have selected: ' + ', '.join(self.selections) + '\nHit any key to continue.')
                screen.getch()
                #screen.refresh()
                screen.clear()

            else:
                try:
                    selectedIndex = int(self.reply)
                    if selectedIndex < 1 : raise IndexError
                    self.selections.append(self.menu.values[selectedIndex - 1])

                    screen.addstr('You have selected: ' + ', '.join(self.selections) + '\nHit any key to continue.')
                    screen.getch()
                    #screen.refresh()
                    screen.clear()
                except IndexError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                        
                except ValueError:
                        screen.addstr('\nYour choice must be a numeric index from the menu. Hit any key to continue.')
                        screen.getch()
                        screen.clear()
                        
                except errors.MenuInputError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()

        buffer.close()
        return self.selections


class TextPrompt:
    def __init__(self, prompt, defaultValue, maxLength=-1):   
          self.text = ''
          self.defaultValue = defaultValue
          if defaultValue is not None: 
                self.prompt = "%s [%s] : " % (prompt, defaultValue)
          else:
                self.prompt = "%s :" % prompt
      
    def show(self, screen):
        screen.clear()
        buffer = StringIO()
        buffer.write('%s\n> ' % self.prompt)
        contents = buffer.getvalue()
        bufferLineArray = contents.split('\n')
        bufferLineCount = len(bufferLineArray)

        cursorRow = bufferLineCount - 1
        cursorColumn = len(bufferLineArray[bufferLineCount - 1])
        
        screen.addstr(buffer.getvalue())
        screen.move(cursorRow, cursorColumn)

        #screen.addstr(">")
        reply = screen.getstr(cursorRow, cursorColumn)
        self.text = reply
        if reply == '': 
            if self.defaultValue is not None:
                self.text = self.defaultValue

        buffer.close()  
        return self.text


class TextSelectPrompt:
    def __init__(self, prompt, allowedValuesDictionary, defaultValue = None):
          self.allowedValuesDictionary = allowedValuesDictionary
          self.selection = None
          self.selectionString = "/".join(self.allowedValuesDictionary.keys())
          self.errorPrompt = "Please select one of the following values: '%s'" % self.selectionString
           
          if defaultValue is None:
              self.prompt = "%s %s :" % (prompt,  self.selectionString)
          else:              
              self.defaultValue = defaultValue
              self.prompt = "%s %s [%s] :" % (prompt, self.selectionString, self.defaultValue)
      
    
    def show(self, screen):
          screen.clear()

          buffer = StringIO()
          buffer.write('%s\n> ' % self.prompt)
          contents = buffer.getvalue()
          bufferLineArray = contents.split('\n')
          bufferLineCount = len(bufferLineArray)
                
          while True:
              cursorRow = bufferLineCount - 1
              cursorColumn = len(bufferLineArray[bufferLineCount - 1])

              screen.addstr(buffer.getvalue())
              screen.move(cursorRow, cursorColumn)              
              reply = screen.getstr(cursorRow, cursorColumn)
              try:
                  if reply == '':
                      if self.defaultValue is None: 
                          raise KeyError
                      else:
                          self.selection = self.allowedValuesDictionary[self.defaultValue]
                          break
                  else:
                      self.reply = reply
                      self.selection = self.allowedValuesDictionary[reply]
                      break
              except KeyError:                        
                  screen.addstr(self.errorPrompt + ". Hit any key to continue.")
                  screen.getch()
                  screen.clear()

          return self.selection


class CursesDisplay:
    def __init__(self, clientClass):
        self.client = clientClass()

    def open(self, **kwargs):
        try:
            # Initialize curses
            screen=curses.initscr()
            # Turn off echoing of keys, and enter cbreak mode,
            # where no buffering is performed on keyboard input
            #curses.noecho()
            curses.cbreak()
            #curses.curs_set(1)

            # In keypad mode, escape sequences for special keys
            # (like the cursor keys) will be interpreted and
            # a special value like curses.KEY_LEFT will be returned
            screen.keypad(1)
            self.client.run(screen, **kwargs)                    # Enter the main loop

            # Set everything back to normal
            screen.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()                 # Terminate curses
        except:
            # In event of error, restore terminal to sane state.
            screen.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
            traceback.print_exc(file = sys.stdout)           # Print the exception
            exit(2)
        
  
