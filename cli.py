#!/usr/bin/python

import os, sys
import curses, traceback
import curses.wrapper
from StringIO import StringIO

class UserInputError: pass

class MenuError: pass

class MenuInputError: pass



class Notice:
    def __init__(self, message):
        self.message = message

    def __str__(self):
        if self.message.__class__.__name__ == 'list':
            return '\n'.join(self.message) + '\n'

        return self.message + '\n'

    def show(self, screen):
    
        if self.message.__class__.__name__ == 'list':
            buffer = StringIO()
            
            #buffer.write('\n'.join(self.message) )
            buffer.write(self.__str__())
            contents = buffer.getvalue()
            bufferLineArray = contents.split('\n')
            bufferLineCount = len(bufferLineArray)
            position = screen.getyx()
            cursorRow = position[0] + bufferLineCount - 1
            cursorColumn = len(bufferLineArray[bufferLineCount-1])
            
            screen.addstr(contents)
            screen.move(cursorRow, cursorColumn)
        else:        
            buffer = StringIO()
            buffer.write('%s' % self.message)
            contents = buffer.getvalue()
            bufferLineArray = contents.split('\n')
            bufferLineCount = len(bufferLineArray)
            
            position = screen.getyx()
            screen.move(position[0], 0)
            screen.addstr(contents)
            position = screen.getyx()
            screen.move(position[0] + 1, 0)




class Menu:
    def __init__(self, options): 
        self._options = options

    def __str__(self):
        index = 1
        entries = []
        for item in self._options:
            entries.append('[%s]\t%s' % (index, item))
            index += 1
        return '\n'.join(entries)

    def addItem(self, itemString):
        self._options.append(itemString)

    def getOptions(self):
        return self._options

    def getOption(self, optionIndex):
        return self._options[optionIndex]

    def getOptionValue(self, optionIndex):
        # TODO: this behavior will change if option labels are mapped
        return self._options[optionIndex]



class MenuPrompt:
    def __init__(self, menu, prompt):
            self.menu = menu            
            self.instructions = [prompt, '(Enter * to exit)']
            self.selectedIndex = -1
            self.selection = ''
            self.escaped = False
            self.reply = ''
    
    def reset(self):
        self.escaped = False
        
               
    def show(self, screen):
            #screen.clear()
            
            buffer = StringIO()
            buffer.write('%s\n\n%s\n:' % (self.menu, '\n'.join(self.instructions)))
            contents = buffer.getvalue()
            bufferLineArray = contents.split('\n')
            bufferLineCount = len(bufferLineArray)
            while True:          
                position = screen.getyx()
                cursorRow = position[0] + bufferLineCount - 1
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
                        self.selection = self.menu.getOption(self.selectedIndex - 1)
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
    def __init__(self, menu, prompt, defaultSelections = [], headerNotice = None):
        self.menu = menu
        
        self.instructions = ["Type * to exit.", "Type # to see the items you've selected.", "Type c to clear your selections."]
        self.instructions.insert(0, prompt)
        self.selections = []
        self.selections.extend(defaultSelections)
        self.escaped = False
        self.selectedIndex = -1
        self.choice = ''
        self.headerNotice = headerNotice


    def reset(self):
        self.escaped = False


    def show(self, screen):
        #screen.clear()
        
        buffer = StringIO()
        buffer.write('%s\n\n%s\n:' % (self.menu, '\n'.join(self.instructions)))
        contents = buffer.getvalue()
        bufferLineArray = contents.split('\n')
        bufferLineCount = len(bufferLineArray)

        while True:
            if self.headerNotice:
                self.headerNotice.show(screen)
            position = screen.getyx()
            cursorRow = position[0] + bufferLineCount - 1
            cursorColumn = len(bufferLineArray[bufferLineCount-1])

            screen.addstr(contents)
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
                newSelections = [int(item.strip()) for item in self.reply.split(',')]
                for selectedIndex in newSelections:
                    try:                        
                        if selectedIndex < 1: 
                            raise IndexError
                        self.selections.append(self.menu.getOption(selectedIndex - 1))
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
                    except MenuInputError:
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
                    self.selections.append(self.menu.getOption(selectedIndex - 1))

                    screen.addstr('\nYou have selected: %s. Hit any key to continue.'  % (', '.join(self.selections)))
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
                        
                except MenuInputError:
                        screen.addstr('\nYou selected a menu index which is not available. Hit any key to continue.')
                        screen.getch()
                        screen.clear()

        buffer.close()
        return self.selections


class TextPrompt:
    def __init__(self, prompt, defaultValue=None, maxLength=-1):   
          self.text = ''
          self.defaultValue = defaultValue
          if defaultValue: 
                self.prompt = "%s [%s] : " % (prompt, defaultValue)
          else:
                self.prompt = "%s :" % prompt
      
    def show(self, screen):
        #screen.clear()
        position = screen.getyx()
        buffer = StringIO()
        buffer.write('%s\n> ' % self.prompt)
        contents = buffer.getvalue()
        bufferLineArray = contents.split('\n')
        bufferLineCount = len(bufferLineArray)

        cursorRow = position[0] + bufferLineCount - 1
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
          self.selectionString = " / ".join(self.allowedValuesDictionary.keys())
          self.errorPrompt = "Please select one of the following values: '%s'" % self.selectionString
          self.defaultValue = defaultValue
          
          if self.defaultValue is None:
              self.prompt = "%s %s :" % (prompt,  self.selectionString)
          else:                            
              self.prompt = "%s %s [%s] :" % (prompt, self.selectionString, self.defaultValue)
      
    
    def show(self, screen):
          #screen.clear()
          
          buffer = StringIO()
          buffer.write('%s\n> ' % self.prompt)
          contents = buffer.getvalue()
          bufferLineArray = contents.split('\n')
          bufferLineCount = len(bufferLineArray)
                
          while True:
              position = screen.getyx()
              cursorRow = position[0] + bufferLineCount - 1
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
    def __init__(self, clientClass, **kwargs ):
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
        
  
