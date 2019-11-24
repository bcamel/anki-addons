#!/usr/bin/python
#-*- coding: utf-8 -*-
#
# Description: Gives a list of example sentences from Tanaka Corpus for the searched expression 
# and generates a cloze card for the chosen sentence, complete with furigana. Generates furigana for custom sentences as well.
# This addon is based on Guillaume VIRY's example sentences plugin for Anki and some code from Pyry KONTIO's Cloze Furigana Tools.
# Version 1.0, released 2014-07-20
#
# Author: Radek SPRTA
# Email: radek.sprta@gmail.com
# License: GNU AGPL


from aqt.qt import QHBoxLayout, QLineEdit, QRect, QDialog, QListWidgetItem, QSize, QStyledItemDelegate, QTextDocument
from aqt.qt import QStyleOptionViewItemV4, QAbstractTextDocumentLayout, QStyle, QApplication
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.utils import showInfo, askUser

from anki.utils import isMac
from anki.hooks import wrap as wrapHook, addHook
from anki.lang import _

from card import installJapaneseSupport, FieldGenerator, MODELNAME
from forms.selectdialog import Ui_selectDialog
from search import Dictionary


class Toolbar(object):
    
    def __init__(self):
            self.dictionary = Dictionary()
            
            def onSetNote(editor, note, hide = True, focus = False):
                # Hides the toolbar when editing different models than MODELNAME 
                try:
                    if MODELNAME.lower() not in note.model()['name'].lower():
                        editor.searchLine.setHidden(True)
                        editor.search.setHidden(True)
                    else:
                        editor.searchLine.setHidden(False)
                        editor.search.setHidden(False)
                except Exception:
                    return
            Editor.setNote = wrapHook(Editor.setNote, onSetNote)
            
            # Setup the toolbar when the editor is being set up        
            addHook("setupEditorButtons", self.addToolbar)
        
    def addToolbar(self, editor):
            self.editor = editor            
            # Do not show the toolbar in Browser window
            # FIXME check if possible to find out entity's type
            if not isinstance(self.editor.parentWindow, Browser):            
                # Add toolbar to the editor           
                self.editor.upperIconsBox = self.editor.iconsBox    
                self.editor.iconsBox = QHBoxLayout()
                if not isMac:
                    self.editor.iconsBox.setMargin(6)
                else:
                    self.editor.iconsBox.setMargin(0)
                self.editor.iconsBox.setSpacing(0)
                self.editor.outerLayout.addLayout(self.editor.iconsBox)
                
                self.editor.searchLine = QLineEdit()
                self.editor.searchLine.setGeometry(QRect(10, 10, 300, 30))
                self.editor.searchLine.setText(u"")
                self.editor.searchLine.setObjectName(u"searchLine")
                self.editor.iconsBox.addWidget(self.editor.searchLine)
                
                self.editor.search = self.editor._addButton("search", lambda: self.openSelectDialog(self.editor.searchLine.text()), tip=_(u"Search for an example sentence for the expression"), text=_(u"Search"), size=False, native=True, canDisable=False)

        
    def openSelectDialog(self, expression):        
        if not expression:
            showInfo(_("Enter a Japanese word to look up an example sentence for."))       
        else:
            # Open the select dialog the there are examples for the searched expression
            if self.dictionary.findExamples(expression)[0]:
                self.editor.dialog = SelectDialog(self, expression)
                self.editor.dialog.show()
            else:
                # If the expression is not in the corpus, offer search on ALC
                if askUser(_(u"No examples found.\nDo you want to search ALC for the expression?")):
                    self.searchAlc(expression)
    
    def searchAlc(self, expression):
        # Uses Japanese Support addon to look the word up on ALC, if it's not installed, asks to download it.
        try:
            from japanese.lookup import Lookup
            Lookup().alc(expression)
        except ImportError:
            installJapaneseSupport()

#Initiate the toolbar
toolbar = Toolbar()
                        

class SelectDialog(QDialog):

    def __init__(self, toolbar, expression):        
        QDialog.__init__(self)
        self.selectDialog = Ui_selectDialog()
        self.selectDialog.setupUi(self)
        
        self.dictionary = toolbar.dictionary
        self.editor = toolbar.editor
        
        # Using custom delegate to render sentences in color
        self.itemDelegate = HTMLDelegate()
        self.selectDialog.listWidget.setItemDelegate(self.itemDelegate)
        
        # Find examples and list them
        self.resultsJapanese, self.resultsEnglish = self.dictionary.findExamples(expression)        
        for sentence in self.resultsJapanese:
            item = QListWidgetItem()
            item.setText(sentence)
            self.selectDialog.listWidget.addItem(item)
            
    def accept(self):       
        exampleEnglish = None
        
        # Return the selected example
        try:        
            exampleJapanese = self.selectDialog.listWidget.selectedItems()[0].text()
        except Exception:  
                showInfo(_(u"Choose an example sentence"))
                return
        exampleJapanese = self.selectDialog.listWidget.currentItem().text()
            
        # Find the English translation for the selected example
        for sentence in self.resultsJapanese:
            if exampleJapanese == sentence:
                exampleEnglish = self.resultsEnglish[self.resultsJapanese.index(sentence)]
        
        # Generate card from the examples and set the focus on the first field
        if FieldGenerator(self.editor.note).generateFields(exampleJapanese, exampleEnglish):
            self.editor.saveNow()
            self.editor.currentField = 0
            self.editor.stealFocus = True
            self.editor.loadNote()

        self.close()


class HTMLDelegate(QStyledItemDelegate):
    
    def paint(self, painter, option, index):
        options = QStyleOptionViewItemV4(option)
        self.initStyleOption(options,index)

        # Choose appropriate style
        style = QApplication.style() if options.widget is None else options.widget.style()

        # Convert text into HTML
        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(option.rect.width())

        options.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, options, painter);

        ctx = QAbstractTextDocumentLayout.PaintContext()

        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItemV4(option)
        self.initStyleOption(options,index)

        # Get sizeof the elements
        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())