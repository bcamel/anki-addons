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



import os
import re
import cPickle
import codecs
import random

from aqt import mw


MAX = 25
FILE = os.path.join(mw.pm.addonFolder(), "japanese_cloze_examples.utf")
FILE_PICKLE = os.path.join(mw.pm.addonFolder(), "japanese_cloze_examples.pickle")


# Modified from Guillaume VIRY's example sentences plugin
class Dictionary():  
 
    def __init__(self):
        self.dictionary = {}         
        
        f = codecs.open(FILE, 'r', 'utf8')
        self.content = f.readlines()
        f.close() 
        
        # Open dictionary file if it exists, build it otherwise
        if (os.path.exists(FILE_PICKLE) and
            os.stat(FILE_PICKLE).st_mtime > os.stat(FILE).st_mtime):
            f = open(FILE_PICKLE, 'rb')
            self.dictionary = cPickle.load(f)
            f.close()
        else:
            self.buildDictionary()
            f = open(FILE_PICKLE, 'wb')
            cPickle.dump(self.dictionary, f, cPickle.HIGHEST_PROTOCOL)
            f.close()
    
    def buildDictionary(self):
        for i, line in enumerate(self.content[1::2]):
            words = set(self.splitter(line)[1:-1])
            for word in words:
                if word.endswith("~"):
                    word = word[:-1]
                if word in self.dictionary and not word.isdigit():
                    self.dictionary[word].append(2*i)
                elif not word.isdigit():
                    self.dictionary[word]=[]
                    self.dictionary[word].append(2*i)
    
    def splitter(self, txt):
        # Split the columns
        txt = re.compile('\s|\[|\]|\(|\{|\)|\}').split(txt)
        for i in range(0,len(txt)):
            if txt[i] == "~":
                txt[i-2] = txt[i-2] + "~"
                txt[i-1] = txt[i-1] + "~"
                txt[i] = ""
        return [x for x in txt if x]
        
    def findExamples(self, expression):
        # Searches for examples only up to the MAX constant
        maxItems = MAX        
        infoQuestion = []
        infoAnswer = []    
        examplesQuestion = []
        examplesAnswer = []           

        if expression in self.dictionary:
            index = self.dictionary[expression]
            index = random.sample(index, min(len(index),maxItems))
            maxItems -= len(index)
            for j in index:
                # Split the example into normal form and one with conjugations
                example = self.content[j].split("#ID=")[0][3:]
                colorExample = self.content[j+1]
                
                regexpConjugated = "(?:\(*%s\)*)(?:\([^\s]+?\))*(?:\[\d+\])*(?:\{(.+?)\})" %expression
                matchConjugated = re.search(regexpConjugated, colorExample)
                regexpReading = "(?:\s([^\s]*?))(?:\(%s\))" % expression
                matchReading = re.search(regexpReading, colorExample)
                # Check if we found the example via dictionary form and highlight the word
                if matchConjugated:
                    colorExpression = matchConjugated.group(1)
                    example = example.replace(colorExpression,'<FONT COLOR="#0000ff">%s</FONT>' % colorExpression)
                # Check if we found the example by reading and highlight the word
                elif matchReading:
                    colorExpression = matchReading.group(1)
                    example = example.replace(colorExpression,'<FONT COLOR="#0000ff">%s</FONT>' % colorExpression)
                # Otherwise the word is in the same form that we searched - just highlight it
                else:
                    example = example.replace(expression,'<FONT COLOR="#0000ff">%s</FONT>' %expression)
                # Adds the Japanese [0] and English [1] sentence containing the expression
                examplesQuestion.append("%s" % example.split('\t')[0])
                examplesAnswer.append("%s" % example.split('\t')[1])
        else:
            # If expression is not in dictionary, try stripping the brackets and slashes
            match = re.search(u"(.*?)[／/]", expression)
            if match:
                return self.findExamples(match.group(1))
    
            match = re.search(u"(.*?)[(（](.+?)[)）]", expression)
            if match:
                if match.group(1).strip():
                    return self.findExamples("%s%s" % (match.group(1), match.group(2)))
        
        # Add sentences found into list
        infoQuestion.extend(examplesQuestion)
        infoAnswer.extend(examplesAnswer)
        return (infoQuestion,infoAnswer)