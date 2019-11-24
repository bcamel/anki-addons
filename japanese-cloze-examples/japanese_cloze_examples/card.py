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

import re 

from aqt import mw
from aqt.utils import showInfo, askUser

from anki.lang import _
from anki.hooks import addHook
import anki.stdmodels
from anki.template.furigana import furigana as furiganaToRuby


JAPANESESUPPORTCODE = "3918629684"
# You can change the field names here
CLOZEFIELD = "Text"
ENGLISHFIELD = "Extra"
FURIGANAFIELD = "Furigana"

MODELNAME = "Japanese Cloze"
# You can change the font size and color here
MODELCSS = u"""
.cloze { font-weight: bold; color: blue; }

.jp { font-size: 30px }
.win .jp { font-family: "MS Mincho", "ＭＳ 明朝"; }
.mac .jp { font-family: "Hiragino Mincho Pro", "ヒラギノ明朝 Pro"; }
.linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
.mobile .jp { font-family: "Hiragino Mincho ProN"; }"""
MODELQUESTION = "\
<span class=jp>{{cloze:Text}}</span><br><br>\n\
{{Extra}}"
MODELANSWER = "<span class=jp>{{furigana:Furigana}}</span><br><br>\
                {{Extra}}"


def addJapaneseClozeModel(col):
        # Add the Japanese Cloze model using the definitions from header    
        models = col.models
        model = models.new(MODELNAME)
        
        field = models.newField(CLOZEFIELD)
        models.addField(model, field)
        field = models.newField(ENGLISHFIELD)
        models.addField(model, field)
        field = models.newField(FURIGANAFIELD)
        models.addField(model, field)
        
        template = models.newTemplate(_("Cloze"))
        model['css'] += MODELCSS
        template['qfmt'] = MODELQUESTION
        template['afmt'] = MODELANSWER
        
        models.addTemplate(model, template)
        models.add(model)        
        return model
        
anki.stdmodels.models.append((MODELNAME, addJapaneseClozeModel))


def installJapaneseSupport():
    # Install the Japanese Support addon
    if askUser(_(u'Japanese Cloze Examples need "Japanese Support" addon to work. Install it now?')):
        from aqt.downloader import download
        ret = download(mw, JAPANESESUPPORTCODE)
        if not ret:
            return False
        data, fname = ret
        mw.addonManager.install(data, fname)
        mw.progress.finish()
        showInfo(_(u"Download successful. Please restart Anki."))
        return True
    else:
        return False


# Generates the fields in the card that is being editted
class FieldGenerator(): 
    
    def __init__(self, note):        
        self.note = note
        self.mecab = ReadingGenerator()
            
    def generateFields(self, exampleJapanese, exampleEnglish):
        # Generates the fields from the given examples
        # Check if reading generator works
        if not self.mecab.japaneseSupportExists():
            return False
        if not self.hasFields():
            return False            
        if not self.canSave():
            return False
        if not self.addReading(exampleJapanese) or not self.addExamples(exampleJapanese, exampleEnglish):
            return False
        return True

    def canSave(self, fields=[CLOZEFIELD, ENGLISHFIELD, FURIGANAFIELD], canOverride=True):
        # Checks if the fields in card are empty. If not, asks user if they want to override it
        empty = True
        for field in fields:
            if self.note[field]:
                empty = False
        if canOverride:
            return (empty or askUser(_(u"Some of the fields are not empty. Override them?")))
        else:
            return empty

    def hasFields(self, srcFields=[CLOZEFIELD, ENGLISHFIELD, FURIGANAFIELD]):
        # Checks if the required fields exist in the model
        fields = []
        for c, name in enumerate(mw.col.models.fieldNames(self.note.model())):
            for field in srcFields:
                if name == field:
                    fields.append(field)
        if len(fields) < len(srcFields):
            return False
        else:
            return True

    def addReading(self, exampleJapanese):
        # Check if the Japanese is installed and works
        if not self.mecab.japaneseSupportExists():
            return False
        # Remove the color tags - would make mess with multiple clozes per sentence
        exampleJapanese = exampleJapanese.replace('<FONT COLOR="#0000ff">',"")
        exampleJapanese = exampleJapanese.replace("</FONT>","")
        # Generate the reading and save it into FURIGANAFIELD
        try:           
            self.note[FURIGANAFIELD] = self.mecab.reading(exampleJapanese)
        except Exception, e:
            self.mecab = None
            raise e
        return True    
               
    def addExamples(self, exampleJapanese, exampleEnglish):
        # Strip the color tags - would make mess with multiple clozes - and add cloze brackets
        exampleJapanese = exampleJapanese.replace('<FONT COLOR="#0000ff">','{{c1::')
        exampleJapanese = exampleJapanese.replace("</FONT>","}}")
        # Save the cloze ready sentence and English translation into CLOZEFIELD and ENGLISHFIELD respectively
        try:        
            self.note[CLOZEFIELD] = exampleJapanese
            self.note[ENGLISHFIELD] = exampleEnglish
        except Exception, e:
            raise e
        return True
        
    def generateReading(self, flag, note, fieldIdx):
        # Generate the reading for cards without it (entered by user without using the search function)
        self.note = note
        # Checks if the Japanese Support reading generator is installed and works
        if not self.mecab.japaneseSupportExists():
            return flag
        # Checks if the model is correct
        if MODELNAME.lower() not in note.model()['name'].lower():
            return flag
        # Checks if the even is coming from the source field
        sourceIdx = None
        for c, name in enumerate(mw.col.models.fieldNames(note.model())):
            for f in [CLOZEFIELD]:
                if name == f:
                    sourceIdx = c
        if fieldIdx != sourceIdx:
            return flag
        # Checks if the source and destination field exist
        if not self.hasFields([CLOZEFIELD, FURIGANAFIELD]):
            return flag
        # Checks if the destination field is empty
        if note[FURIGANAFIELD]:
            return flag
            
        # Grab the source text
        source = mw.col.media.strip(note[CLOZEFIELD])
        # Remove the cloze brackets
        source = source.replace("}}","")
        source = re.sub(r"\{\{c\d+::", "", source)
        if not source:
            return flag
        # Generate the reading and add it to the field
        try:
            self.addReading(source)
        except Exception, e:
            self.mecab = None
            raise e
        return True
        

# Generate furigana for custom sentences
def onFocusLost(flag, note, fieldIdx):
    return FieldGenerator(note).generateReading(flag, note, fieldIdx)
    
addHook("editFocusLost", onFocusLost)


# Wrapper for mecab reading generator from Japanese Support plugin
class ReadingGenerator():
    
    def __init__(self):
        # The Japanese Support plugin reading module method patched by Pyry KONTIO 
        def _reading(self, expr):
        	self.ensureOpen()
        	self.mecab.stdin.write(expr.replace(' ', '_BSP_').replace(u'\u00a0', '_NBSP_').encode("euc-jp", "ignore")+'\n')
        	self.mecab.stdin.flush()
        	expr = unicode(self.mecab.stdout.readline().rstrip('\r\n'), "euc-jp").replace('_NBSP_', u'\u00a0').replace('_BSP_', ' ')
        	out = []
        	inNode = False
        	for node in re.split(ur"( [^ ]+?\[.*?\])", expr):
        		if not inNode:
        			out.append(node)
        			inNode = True
        			continue
        		else:
        			(kanji, reading) = re.match(ur" (.+?)\[(.*?)\]", node, flags=re.UNICODE).groups()
        			inNode = False
        		# hiragana, punctuation, not japanese, or lacking a reading
        		if kanji == reading or not reading:
        			out.append(kanji)
        			continue
        		# katakana
        		if kanji == japanese.reading.kakasi.reading(reading):
        			out.append(kanji)
        			continue
        		# convert to hiragana
        		reading = japanese.reading.kakasi.reading(reading)
        		# ended up the same
        		if reading == kanji:
        			out.append(kanji)
        			continue
        		# don't add readings of numbers
        		if kanji in u"一二三四五六七八九十０１２３４５６７８９":
        			out.append(kanji)
        			continue
        		# strip matching characters and beginning and end of reading and kanji
        		# reading should always be at least as long as the kanji
        		placeL = 0
        		placeR = 0
        		for i in range(1,len(kanji)):
        			if kanji[-i] != reading[-i]:
        				break
        			placeR = i
        		for i in range(0,len(kanji)-1):
        			if kanji[i] != reading[i]:
        				break
        			placeL = i+1
        		if placeL == 0:
        			if placeR == 0:
        				out.append(" %s[%s]" % (kanji, reading))
        			else:
        				out.append(" %s[%s]%s" % (
        					kanji[:-placeR], reading[:-placeR], reading[-placeR:]))
        		else:
        			if placeR == 0:
        				out.append("%s %s[%s]" % (
        					reading[:placeL], kanji[placeL:], reading[placeL:]))
        			else:
        				out.append("%s %s[%s]%s" % (
        					reading[:placeL], kanji[placeL:-placeR],
        					reading[placeL:-placeR], reading[-placeR:]))
        	fin = u""
        	fin = ''.join(out)
        	return fin
        try:
            import japanese.reading
            japanese.reading.mecabArgs = ['--node-format= %m[%f[7]]', '--eos-format=\n', '--unk-format=%m']
            japanese.reading.MecabController.reading = _reading
            self.mecab = japanese.reading.MecabController()
        except ImportError:
            self.mecab = None
            self.japaneseSupportExists()
        
    def japaneseSupportExists(self):
        # Downloads the Japanese Support plugin if not already installed
        if not self.mecab:
            installJapaneseSupport()
            return False
        else:
        	return True
    
    def reading(self, expression):
        return self.mecab.reading(expression)        

        
def highlightClozes(html, type, fields, model, data, col):
    # Regular expression for finding the clozed expressions, i.e {{c1::example}}
    cloze = r"\{\{c%s::(.*?)\}\}"
    # Styles given word as cloze
    style = "<span class=cloze>%s</span>"
   
    # Checks if the model is correct
    if MODELNAME.lower() not in model['name'].lower():
        return html
    # Checks if the source fields exist
    if CLOZEFIELD not in fields or FURIGANAFIELD not in fields:
        return html
    # Checks if the Furigana field is not empty. Cloze field is covered by Anki itself.
    if not fields[FURIGANAFIELD]:
        return u"The %s field is empty. Please edit this note and generate the reading." % FURIGANAFIELD
               
    # An implementation which allows user-editted readings    
    if re.search(cloze % str(data[4]+1), fields[CLOZEFIELD]):
        # Finds which cloze is being reviewed (cloze number data[4]+1) and returns the word with reading for it, if it exists
        word = re.search(cloze % str(data[4]+1), ReadingGenerator().reading(fields[CLOZEFIELD])).group(1)
                
        results = []        
        subgroups = []
        furiganaBrackets = r"\[(.*?)\]"
        
        # Split the word into subgroups and strip the furigana from them
        for split in word.split(" "):
            if re.search(furiganaBrackets, split):
                subgroups.append(re.sub(furiganaBrackets, "", split))    
        
        # Split the reading into columns
        columns = fields[FURIGANAFIELD].split(" ")
        if subgroups:
            # For each column, check if it contains a subgroup. If it does, get the potentially user editted reading
            # and update it in the word
            for column in columns:
                nofurigana = re.sub(furiganaBrackets, "", column)
                match = re.search(furiganaBrackets, column)                
                for subgroup in subgroups:
                    if re.search(subgroup, nofurigana):                        
                        results.append(re.sub(subgroup + furiganaBrackets, "%s[%s]" % (subgroup, match.group(1)), word))
                        
        # There was no furigana, use the word as it is
        if not results:
            results.append(word)
        # Using furiganaToRuby find the word in card and substitute it for the version styled as cloze
        for result in results:
            html = re.sub(furiganaToRuby(result), style % furiganaToRuby(result), html)            
    return html
    
# Calls highlightClozes when card is being rendered
addHook("mungeQA", highlightClozes)