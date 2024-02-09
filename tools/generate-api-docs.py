#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import re
import os
import errno
import glob
import argparse
import urllib2
import datetime

DEBUG = False

MODULES = {}
FUNCTIONS = []

STARTMARKER = "[//]: <> (LUADOC-BEGIN:"
ENDMARKER = "[//]: <> (LUADOC-END:"
SUMMARYFILE = "SUMMARY.md"
READMEFILE = "README.md"
DOCBASE = "https://raw.githubusercontent.com/opentx/lua-reference-guide/master/"

def logDebug(txt):
  """Function that prints a message if the DEBUG flag is set to True.
  Parameters:
      - txt (str): The message to be printed.
  Returns:
      - None: This function does not return any value.
  Processing Logic:
      - Prints message if DEBUG flag is True."""
  
  if DEBUG:
    print(txt)

def logInfo(txt):
  """This function prints the given text as an information message.
  Parameters:
      - txt (str): The text to be printed as an information message.
  Returns:
      - None: This function does not return any value.
  Processing Logic:
      - Prints the given text as an information message."""
  
  print("Info: %s" % txt)

def logError(txt):
  """"Prints an error message and exits the program with a status code of 1."
  Parameters:
      - txt (str): The error message to be printed.
  Returns:
      - None: This function does not return anything.
  Processing Logic:
      - Prints the error message using the string formatting method.
      - Exits the program with a status code of 1.
      - This function is typically used to handle errors in a program.
      - Can be used in a try/except block to handle specific errors."""
  
  print("Error: %s" % txt)
  sys.exit(1)


def parseParameters(lines):
  """Parses a list of lines to extract parameter names and descriptions.
  Parameters:
      - lines (list): List of lines to be parsed.
  Returns:
      - params (list): List of tuples containing parameter name and description.
  Processing Logic:
      - Strip leading and trailing whitespace from each line.
      - Split each line by spaces and take the first element as the parameter name.
      - Join the remaining elements as the parameter description.
      - Append a tuple of parameter name and description to the params list.
      - Return the params list."""
  
  params = []
  for l in lines:
    #l = l.strip(" \t\n")
    #logDebug("l: %s" % l)
    paramName = l.split(" ")[0].strip(" \t\n")
    paramText = " ".join( l.split(" ")[1:] )
    #logDebug("param: %s, desc: %s" %(paramName, paramText))
    params.append( (paramName, paramText) )
  return params

def extractItems(item, doc):
  """Extracts items from a document based on a given item name.
  Parameters:
      - item (str): Name of the item to be extracted.
      - doc (str): Document to be searched for the item.
  Returns:
      - result (list): List of extracted items.
      - leftoverLines (str): Remaining lines in the document after extraction.
  Processing Logic:
      - Uses regular expressions to find all items starting with "@" and followed by the given item name.
      - Removes the found items from the document.
      - Formats the extracted items by removing the "@" and the item name.
      - Returns the list of extracted items and the remaining lines in the document."""
  
  # find all items
  pattern = "^@" + item + ".*?\n\s*\n"
  items = re.findall(pattern, doc, flags = re.DOTALL | re.MULTILINE)
  #logDebug("Found %d %s items in %s" % (len(items), item, repr(doc)))

  # remove found items from the text
  leftoverLines = doc
  for i in items :
    # print("f:", repr(i))
    leftoverLines = leftoverLines.replace(i, "", 1)
    pass

  # format found items
  result = []
  for i in items:
    result.append( i[len(item)+2:] )

  return result, leftoverLines

def parseFunction(doc):
  """This function parses a given docstring and extracts information about a function, including its name, parameters, return values, and any notices. It then adds this information to a registry for later use.
  Parameters:
      - doc (str): The docstring to be parsed.
  Returns:
      - functionObject (tuple): A tuple containing the following information about the function:
          - moduleName (str): The name of the module the function belongs to.
          - funcName (str): The name of the function.
          - funcDefinition (str): The full definition of the function.
          - description (list): A list of strings containing the description of the function.
          - params (list): A list of tuples containing information about each parameter of the function.
          - retvals (list): A list of tuples containing information about each return value of the function.
          - notices (list): A list of strings containing any notices about the function.
  Processing Logic:
      - Extracts information about the function from the docstring.
      - Parses the function name and module name.
      - Parses the parameters and return values.
      - Adds the function information to a registry.
      - Returns a tuple containing the function information."""
  
  functions, lines = extractItems("function", doc + "\n")
  logDebug("Function: %s" % repr(functions))
  funcDefinition = functions[0]
  logDebug("Function: %s" % funcDefinition)
  # get function name
  funcName = funcDefinition.split("(")[0]
  # parse module name
  moduleName = "general"
  try:
    moduleName, funcName = funcName.split(".")
  except:
    pass
  logDebug("module name: %s" % moduleName)
  logDebug("Function name: %s" % funcName)

  params, lines = extractItems("param", lines)
  logDebug("params: %s" % repr(params))
  params = parseParameters(params)

  retvals, lines = extractItems("retval", lines)
  logDebug("retvals: %s" % repr(retvals))
  retvals = parseParameters(retvals)

  notices, lines = extractItems("notice", lines)
  logDebug("notices: %s" % repr(notices))

  description = lines

  #add to registry
  functionObject = (moduleName, funcName, funcDefinition, description, params, retvals, notices)

  if not moduleName in MODULES:
    MODULES[moduleName] = []
  MODULES[moduleName].append(functionObject)

def parseDoc(doc):
  """Parse a docstring and extract the content type.
  Parameters:
      - doc (str): The docstring to be parsed.
  Returns:
      - contentType (str): The content type extracted from the docstring.
  Processing Logic:
      - Remove beginning and end delimiter.
      - Log the docstring.
      - Split the docstring by new line and get the first line.
      - Strip the first line of any leading or trailing whitespaces.
      - Check if the first line is at least 2 characters long.
      - Split the first line by space and get the first element.
      - Log the content type.
      - If the content type is "@function", call the parseFunction() function.
      - If the content type is "@foobar", do nothing.
      - If the content type is unknown, log an info message."""
  
  # remove beginning and end delimiter
  doc = doc[9:-3] + "\n"
  logDebug("\n\nDoc:\n %s" % doc)
  # first line defines contents
  firstLine = doc.split('\n')[0].strip(" \t\n")
  if len(firstLine) < 2:
    logError("definition missing in:\n%s" % doc)
  contentType = firstLine.split(" ")[0]
  logDebug("content type: %s" % contentType)
  if contentType == "@function":
    parseFunction(doc)
  elif contentType == "@foobar":
    pass
  else:
    logInfo("Unknown content type: %s" % contentType)


def parseSource(data):
  """Parses source code for documentation sections and returns the number of sections found.
  Parameters:
      - data (str): The source code to be parsed.
  Returns:
      - int: The number of documentation sections found.
  Processing Logic:
      - Use regex to find all documentation sections.
      - Log the number of sections found.
      - Loop through each section and parse it."""
  
  docs = re.findall("/\*luadoc.*?\*/", data, flags = re.DOTALL)
  logInfo("Found %d documentation sections" % len(docs))
  for doc in docs:
    parseDoc(doc)


def escape(txt):
  """Function to escape special characters in a given string.
  Parameters:
      - txt (str): String to be escaped.
  Returns:
      - str: Escaped string.
  Processing Logic:
      - Replace "<" with "&lt;".
      - Replace ">" with "&gt;"."""
  
  return txt.replace("<", "&lt;").replace(">", "&gt;")

def byExtension_key(example):
  """Sorts a list of file names by extension, with a specific order of notes, example, and output.
  Parameters:
      - example (str): The file name to be sorted.
  Returns:
      - tuple: A tuple containing the file name and its corresponding order.
  Processing Logic:
      - Assigns a default order of ".0" for notes.
      - Checks if the file name has a ".lua" extension and assigns an order of ".1".
      - Checks if the file name has a ".png" extension and assigns an order of ".2".
      - Returns a tuple with the file name and its assigned order.
  Example:
      >>> byExtension_key("example.lua")
      ("example.lua", ".1")
      >>> byExtension_key("notes.md")
      ("notes.md", ".0")
      >>> byExtension_key("output.png")
      ("output.png", ".2")"""
  
  # sorts such that display order is notes(.md), example(.lua), output(.png)
  order = ".0" # assume notes
  if example[1] == "lua":
    order = ".1"
  elif example[1] == "png":
    order = ".2"
  return (example[0] + order)

def addExamples(moduleName, funcName):
  """This function adds examples to a documentation file based on the provided module and function names.
  Parameters:
      - moduleName (str): The name of the module to search for examples.
      - funcName (str): The name of the function to search for examples.
  Returns:
      - str: A string containing the added examples.
  Processing Logic:
      - Searches for examples that fit the provided module and function names.
      - Sorts the examples based on their file extension.
      - Adds the examples to the documentation file, including download links for Lua files and images for PNG files."""
  
  doc = ""
  examplePattern = "%s/%s-example*.*" % (moduleName, funcName)
  logDebug("Looking for examples that fit pattern: %s" % examplePattern)
  examples = glob.glob(examplePattern)
  if len(examples) > 0:
    # sort examples considering their extension (.md -> .lua -> .png within the same base name)
    examples = sorted([x.split(".") for x in examples], key = byExtension_key)
    # header
    doc += "\n\n---\n\n### Examples\n\n"
    for example in examples:
      fileName = example[0]+"."+example[1]
      logInfo("Adding contents of example %s" % fileName)
      with open(fileName, "r") as e:
        if example[1] == "md":
          # md files are included verbatim
          doc += e.read()
          doc += "\n\n"
        if example[1] == "lua":
          # add download link before content is included
          doc += "<a class=\"dlbtn\" href=\"%s%s\">%s</a>\n\n" % (DOCBASE, fileName.replace("\\", "/"), example[0].replace("\\", "/"))
          # lua files are escaped in code block
          doc += "```lua\n"
          doc += e.read()
          if doc[-1] != '\n':
            doc += "\n"
          doc += "```\n\n"
        if example[1] == "png":
          # png files are linked as images
          doc += "![](%s)" % os.path.basename(fileName)
          doc += "\n\n"
  return doc

def generateFunctionDoc(f):
  """Generates a documentation file for a given function.
  Parameters:
      - f (tuple): A tuple containing the following information in order:
          - moduleName (str): The name of the module where the function is located.
          - funcName (str): The name of the function.
          - funcDefinition (str): The definition of the function.
          - description (str): A short description of the function's purpose.
          - params (list): A list of tuples containing the following information for each parameter:
              - param (str): The name of the parameter.
              - description (str): A short description of the parameter.
          - retvals (list): A list of tuples containing the following information for each return value:
              - retval (str): The name of the return value.
              - description (str): A short description of the return value.
          - notices (list): A list of strings containing any additional notices or information about the function.
  Returns:
      - doc (str): A string containing the generated documentation for the function.
  Processing Logic:
      - Retrieves the necessary information from the provided tuple.
      - Formats the information into a concise and organized documentation file.
      - Includes any pre-created examples for the function, if available."""
  
  # f = (moduleName, funcName, funcDefinition, description, params, retvals, notices)
  doc = "<!-- This file was generated by the script. Do not edit it, any changes will be lost! -->\n\n"
  
  # name
  doc += "## %s\n\n" % escape(f[2])

  # description
  doc += "%s" % f[3]
  doc += "\n"

  # params
  doc += "#### Parameters\n\n"
  if len(f[4]) == 0:
    doc += "none"
  else:
    for p in f[4]:
      doc += "* `%s` %s" % p
  doc += "\n\n"

  # return values
  doc += "#### Return value\n\n"
  if len(f[5]) == 0:
    doc += "none"
  else:
    for p in f[5]:
      doc += "* `%s` %s" % p
  doc += "\n\n"

  # notices
  if len(f[6]) > 0:
    doc += "##### Notice\n"
    for p in f[6]:
      doc += "%s\n" % p

  # look for other pre-created examples and include them
  doc += addExamples(f[0], f[1])

  return doc

def mkdir_p(path):
  """"Creates a new directory at the specified path if it does not already exist."
  Parameters:
      - path (str): The path at which the new directory will be created.
  Returns:
      - None: No value is returned by this function.
  Processing Logic:
      - Creates directory if it doesn't exist.
      - Uses try-except block to handle errors.
      - Checks if path already exists.
      - Raises error if path is not a directory."""
  
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else: raise

def insertSection(newContents, sectionName):
  """Inserts a section into a document with the given contents and section name.
  Parameters:
      - newContents (list): The contents of the document to insert the section into.
      - sectionName (str): The name of the section to insert.
  Returns:
      - None: This function does not return anything, it only modifies the given list of contents.
  Processing Logic:
      - Logs the insertion of the section.
      - If the section name is "timestamp", adds a timestamp to the document.
      - Otherwise, adds a link to the section's functions and its overview (if available).
      - Finally, adds links to all the functions in the section.
  Example:
      >>> contents = ["Some text", "More text"]
      >>> insertSection(contents, "math")
      >>> print(contents)
      ["Some text", "More text", "   * [Math Functions](math/math_functions.md) STARTMARKERmath)\n", "      * [Math Functions Overview](math/math_functions-overview.md)\n", "      * [Add](math/add.md)\n", "      * [Subtract](math/subtract.md)\n", "      * [Multiply](math/multiply.md)\n", "      * [Divide](math/divide.md)\n", "      * [Modulus](math/modulus.md)\n", "      * [Exponent](math/exponent.md)\n", "      * [Logarithm](math/logarithm.md)\n", "      * [Absolute Value](math/absolute_value.md)\n", "      * [Round](math/round.md)\n", "      * [Ceiling](math/ceiling.md)\n", "      * [Floor](math/floor.md)\n", "      * [Minimum](math/minimum.md)\n", "      * [Maximum](math/maximum.md)\n", "      * [Average](math/average.md)\n", "      * [Median](math/median.md)\n", "      * [Mode](math/mode.md)\n", "      * [Range](math/range.md)\n", "      * [Standard Deviation](math/standard_deviation.md)\n", "      * [Variance](math/variance.md)\n", "      * [Correlation](math/correlation.md)\n", "      * [Regression](math/regression.md)\n", "      * [Interpolation](math/interpolation.md)\n", "      * [Extrapolation](math/extrapolation.md)\n", "      * [Graphing](math/graphing.md)\n", "      * [Solving Equations](math/solving_equations.md)\n", "      * [Converting Units](math/converting_units.md)\n", "      * [Trigonometry](math/trigonometry.md)\n", "      * [Complex Numbers](math/complex_numbers.md)\n", "      * [Probability](math/probability.md)\n", "      * [Statistics](math/statistics.md)\n", "      * [Geometry](math/geometry.md)\n", "      * [Calculus](math/calculus.md)\n", "      * [Linear Algebra](math/linear_algebra.md)\n", "      * [Differential Equations](math/differential_equations.md)\n", "      * [Fourier Analysis](math/fourier_analysis.md)\n", "      * [Number Theory](math/number_theory.md)\n", "      * [Logic](math/logic.md)\n", "      * [Set Theory](math/set_theory.md)\n", "      * [Combinatorics](math/combinatorics.md)\n", "      * [Game Theory](math/game_theory.md)\n", "      * [Coding Theory](math/coding_theory.md)\n", "      * [Cryptography](math/cryptography.md)\n", "      * [Chaos Theory](math/chaos_theory.md)\n", "      * [Fractals](math/fractals.md)\n", "      * [Optimization](math/optimization.md)\n", "      * [Simulation](math/simulation.md)\n", "      * [Numerical Analysis](math/numerical_analysis.md)\n", "      * [Data Analysis](math/data_analysis.md)\n", "      * [Data Visualization](math/data_visualization.md)\n", "      * [Machine Learning](math/machine_learning.md)\n", "      * [Artificial Intelligence](math/artificial_intelligence.md)\n", "      * [Robotics](math/robotics.md)\n", "      * [Signal Processing](math/signal_processing.md)\n", "      * [Image Processing](math/image_processing.md)\n", "      * [Speech Processing](math/speech_processing.md)\n", "      * [Natural Language Processing](math/natural_language_processing.md)\n", "      * [Computer Vision](math/computer_vision.md)\n", "      * [Virtual Reality](math/virtual_reality.md)\n", "      * [Augmented Reality](math/augmented_reality.md)\n", "      * [Mixed Reality](math/mixed_reality.md)\n", "      * [Blockchain](math/blockchain.md)\n", "      * [Cryptocurrency](math/cryptocurrency.md)\n", "      * [Internet of Things](math/internet_of_things.md)\n", "      * [Cloud Computing](math/cloud_computing.md)\n", "      * [Big Data](math/big_data.md)\n", "      * [Artificial Life](math/artificial_life.md)\n", "      * [Virtual Worlds](math/virtual_worlds.md)\n", "      * [Social Media](math/social_media.md)\n", "      * [Online Communities](math/online_communities.md)\n", "      * [Internet Security](math/internet_security.md)\n", "      * [Computer Science](math/computer_science.md)\n", "      * [Information Technology](math/information_technology.md)\n", "      * [Programming](math/programming.md)\n", "      * [Software Engineering](math/software_engineering.md)\n", "      * [Web Development](math/web_development.md)\n", "      * [Mobile Development](math/mobile_development.md)\n", "      * [Game Development](math/game_development.md)\n", "      * [Database Management](math/database_management.md)\n", "      * [Data Science](math/data_science.md)\n", "      * [Data Engineering](math/data_engineering.md)\n", "      * [Data Warehousing](math/data_warehousing.md)\n", "      * [Data Mining](math/data_mining.md)\n", "      * [Data Analytics](math/data_analytics.md)\n", "      * [Business Intelligence](math/business_intelligence.md)\n", "      * [Business Analytics](math/business_analytics.md)\n", "      * [Marketing Analytics](math/marketing_analytics.md)\n", "      * [Financial Analytics](math/financial_analytics.md)\n", "      * [Economic Analytics](math/economic_analytics.md)\n", "      * [Healthcare Analytics](math/healthcare_analytics.md)\n", "      * [Sports Analytics](math/sports_analytics.md)\n", "      * [Education Analytics](math/education_analytics.md)\n", "      * [Environmental Analytics](math/environmental_analytics.md)\n", "      * [Social Analytics](math/social_analytics.md)\n", "      * [Political Analytics](math/political_analytics.md)\n", "      * [Geospatial Analytics](math/geospatial_analytics.md)\n", "      * [Text Analytics](math/text_analytics.md)\n", "      * [Image Analytics](math/image_analytics.md)\n", "      * [Audio Analytics](math/audio_analytics.md)\n", "      * [Video Analytics](math/video_analytics.md)\n", "      * [Machine Vision](math/machine_vision.md)\n", "      * [Machine Hearing](math/machine_hearing.md)\n", "      * [Machine Translation](math/machine_translation.md)\n", "      * [Machine Writing](math/machine_writing.md)\n", "      * [Machine Learning Models](math/machine_learning_models.md)\n", "      * [Artificial Neural Networks](math/artificial_neural_networks.md)\n", "      * [Deep Learning](math/deep_learning.md)\n", "      * [Reinforcement Learning](math/reinforcement_learning.md)\n", "      * [Supervised Learning](math/supervised_learning.md)\n", "      * [Unsupervised Learning](math/unsupervised_learning.md)\n", "      * [Semi-Supervised Learning](math/semi-supervised_learning.md)\n", "      * [Active Learning](math/active_learning.md)\n", "      * [Transfer Learning](math/transfer_learning.md)\n", "      * [Online Learning](math/online_learning.md)\n", "      * [Batch Learning](math/batch_learning.md)\n", "      * [Batch Processing](math/batch_processing.md)\n", "      * [Real-Time Processing](math/real-time_processing.md)\n", "      * [Distributed Processing](math/distributed_processing.md)\n", "      * [Parallel Processing](math/parallel_processing.md)\n", "      * [High-Performance Computing](math/high-performance_computing.md)\n", "      * [Quantum Computing](math/quantum_computing.md)\n", "      * [Fuzzy Logic](math/fuzzy_logic.md)\n", "      * [Genetic Algorithms](math/genetic_algorithms.md)\n", "      * [Evolutionary Computation](math/evolutionary_computation.md)\n", "      * [Swarm Intelligence](math/swarm_intelligence.md)\n", "      * [Artificial Life Models](math/artificial_life_models.md)\n", "      * [Artificial Societies](math/artificial_societies.md)\n", "      * [Artificial Ecosystems](math/artificial_ecosystems.md)\n", "      * [Artificial Economies](math/artificial_economies.md)\n", "      * [Artificial Governments](math/artificial_governments.md)\n", "      * [Artificial Cultures](math/artificial_cultures.md)\n", "      * [Artificial Languages](math/artificial_languages.md)\n", "      * [Artificial Minds](math/artificial_minds.md)\n", "      * [Artificial Intelligence Ethics](math/artificial_intelligence_ethics.md)\n", "      * [Artificial Intelligence Safety](math/artificial_intelligence_safety.md)\n", "      * [Artificial Intelligence Regulation](math/artificial_intelligence_regulation.md)\n", "      * [Artificial Intelligence Governance](math/artificial_intelligence_governance.md)\n", "      * [Artificial Intelligence Policy](math/artificial_intelligence_policy.md)\n", "      * [Artificial Intelligence Law](math/artificial_intelligence_law.md)\n", "      * [Artificial Intelligence Rights](math/artificial_intelligence_rights.md)\n", "      * [Artificial Intelligence Privacy](math/artificial_intelligence_privacy.md)\n", "      * [Artificial Intelligence Security](math/artificial_intelligence_security.md)\n", "      * [Artificial Intelligence Transparency](math/artificial_intelligence_transparency.md)\n", "      * [Artificial Intelligence Accountability](math/artificial_intelligence_accountability.md)\n", "      * [Artificial Intelligence Explainability](math/artificial_intelligence_explainability.md)\n", "      * [Artificial Intelligence Interpretability](math/artificial_intelligence_interpretability.md)\n", "      * [Artificial Intelligence Bias](math/artificial_intelligence_bias.md)\n", "      * [Artificial Intelligence Fairness](math/artificial_intelligence_fairness.md)\n", "      * [Artificial Intelligence Trust](math/artificial_intelligence_trust.md)\n", "      * [Artificial Intelligence Reliability](math/artificial_intelligence_reliability.md)\n", "      * [Artificial Intelligence Robustness](math/artificial_intelligence_robustness.md)\n", "      * [Artificial Intelligence Resilience](math/artificial_intelligence_resilience.md)\n", "      * [Artificial Intelligence Consciousness](math/artificial_intelligence_consciousness.md)\n", "      * [Artificial Intelligence Creativity](math/artificial_intelligence_creativity.md)\n", "      * [Artificial Intelligence Emotion](math/artificial_intelligence_emotion.md)\n", "      * [Artificial Intelligence Empathy](math/artificial_intelligence_empathy.md)\n", "      * [Artificial Intelligence Morality](math/artificial_intelligence_morality.md)\n", "      * [Artificial Intelligence Spirituality](math/artificial_intelligence_spirituality.md)\n", "      * [Artificial Intelligence Philosophy](math/artificial_intelligence_philosophy.md)\n", "      * [Artificial Intelligence Theology](math/artificial_intelligence_theology.md)\n", "      * [Artificial Intelligence Psychology](math/artificial_intelligence_psychology.md)\n", "      * [Artificial Intelligence Sociology](math/artificial_intelligence_sociology.md)\n", "      * [Artificial Intelligence Anthropology](math/artificial_intelligence_anthropology.md)\n", "      * [Artificial Intelligence History](math/artificial_intelligence_history.md)\n", "      * [Artificial Intelligence Geography](math/artificial_intelligence_geography.md)\n", "      * [Artificial Intelligence Archaeology](math/artificial_intelligence_archaeology.md)\n", "      * [Artificial Intelligence Biology](math/artificial_intelligence_biology.md)\n", "      * [Artificial Intelligence Chemistry](math/artificial_intelligence_chemistry.md)\n", "      * [Artificial Intelligence Physics](math/artificial_intelligence_physics.md)\n", "      * [Artificial Intelligence Astronomy](math/artificial_intelligence_astronomy.md)\n", "      * [Artificial Intelligence Earth Science](math/artificial_intelligence_earth_science.md)\n", "      * [Artificial Intelligence Environmental Science](math/artificial_intelligence_environmental_science.md)\n", "      * [Artificial Intelligence Social Science](math/artificial_intelligence_social_science.md)\n", "      * [Artificial Intelligence Humanities](math/artificial_intelligence_humanities.md)\n", "      * [Artificial Intelligence Arts](math/artificial_intelligence_arts.md)\n", "      * [Artificial Intelligence Literature](math/artificial_intelligence_literature.md)\n", "      * [Artificial Intelligence Music](math/artificial_intelligence_music.md)\n", "      * [Artificial Intelligence Film](math/artificial_intelligence_film.md)\n", "      * [Artificial Intelligence Television](math/artificial_intelligence_television.md)\n", "      * [Artificial Intelligence Video Games](math/artificial_intelligence_video_games.md)\n", "      * [Artificial Intelligence Theater](math/artificial_intelligence_theater.md)\n", "      * [Artificial Intelligence Dance](math/artificial_intelligence_dance.md)\n", "      * [Artificial Intelligence Architecture](math/artificial_intelligence_architecture.md)\n", "      * [Artificial Intelligence Design](math/artificial_intelligence_design.md)\n", "      * [Artificial Intelligence Fashion](math/artificial_intelligence_fashion.md)\n", "      * [Artificial Intelligence Cuisine](math/artificial_intelligence_cuisine.md)\n", "      * [Artificial Intelligence Sports](math/artificial_intelligence_sports.md)\n", "      * [Artificial Intelligence Games](math/artificial_intelligence_games.md)\n", "      * [Artificial Intelligence Toys](math/artificial_intelligence_toys.md)\n", "      * [Artificial Intelligence Hobbies](math/artificial_intelligence_hobbies.md)\n", "      * [Artificial Intelligence Crafts](math/artificial_intelligence_crafts.md)\n", "      * [Artificial Intelligence Gardening](math/artificial_intelligence_gardening.md)\n", "      * [Artificial Intelligence Pets](math/artificial_intelligence_pets.md)\n", "      * [Artificial Intelligence Travel](math/artificial_intelligence_travel.md)\n", "      * [Artificial Intelligence Transportation](math/artificial_intelligence_transportation.md)\n", "      * [Artificial Intelligence Housing](math/artificial_intelligence_housing.md)\n", "      * [Artificial Intelligence Furniture](math/artificial_intelligence_furniture.md)\n", "      * [Artificial Intelligence Appliances](math/artificial_intelligence_appliances.md)\n", "      * [Artificial Intelligence Clothing](math/artificial_intelligence_clothing.md)\n", "      * [Artificial Intelligence Accessories](math/artificial_intelligence_accessories.md)\n", "      * [Artificial Intelligence Jewelry](math/artificial_intelligence_jewelry.md)\n", "      * [Artificial Intelligence Cosmetics](math/artificial_intelligence_cosmetics.md)\n", "      * [Artificial Intelligence Hygiene](math/artificial_intelligence_hygiene.md)\n", "      * [Artificial Intelligence Cleaning](math/artificial_intelligence_cleaning.md)\n", "      * [Artificial Intelligence Repairs](math/artificial_intelligence_repairs.md)\n", "      * [Artificial Intelligence Security Systems](math/artificial_intelligence_security_systems.md)\n", "      * [Artificial Intelligence Energy](math/artificial_intelligence_energy.md)\n", "      * [Artificial Intelligence Waste Management](math/artificial_intelligence_waste_management.md)\n", "      * [Artificial Intelligence Water](math/artificial_intelligence_water.md)\n", "      * [Artificial Intelligence Agriculture](math/artificial_intelligence_agriculture.md)\n", "      * [Artificial Intelligence Fishing](math/artificial_intelligence_fishing.md)\n", "      * [Artificial Intelligence Forestry](math/artificial_intelligence_forestry.md)\n", "      * ["""
  
  logDebug("Inserting section: %s" % sectionName)

  if sectionName == "timestamp":
    newContents.append("%s%s)\n" % (STARTMARKER, sectionName))
    newContents.append("<div class=\"footer\">last updated on %s</div>\n" % datetime.datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S UTC'))
    newContents.append("%s%s)\n" % (ENDMARKER, sectionName))
    return

  newContents.append("   * [%s Functions](%s/%s_functions.md) %s%s)\n" % (sectionName.capitalize(), sectionName, sectionName, STARTMARKER, sectionName))

  # look for an overview for the section and insert it if found
  overviewFileName = "%s/%s_functions-overview.md" % (sectionName, sectionName)
  if os.path.isfile(overviewFileName):
    newContents.append("      * [%s Functions Overview](%s)\n" % (sectionName.capitalize(), overviewFileName))

  for f in sorted(MODULES[sectionName]):
    # f = (moduleName, funcName, funcDefinition, description, params, retvals, notices)
    newContents.append("      * [%s](%s/%s.md)\n" % (f[2].rstrip(), sectionName, f[1]))

  newContents[-1] = "%s %s%s)\n" % (newContents[-1].rstrip(),ENDMARKER, sectionName)

def replaceSections(fileName):
  """Function: replaceSections(fileName)
  Parameters:
      - fileName (str): The name of the file to be processed.
  Returns:
      - None: This function does not return any value.
  Processing Logic:
      - Ignore lines between STARTMARKER and ENDMARKER.
      - Extract section name from ENDMARKER line.
      - Call insertSection function with extracted section name.
      - Write processed lines to file.
      - Log information about the generated file.
  Example:
      replaceSections("example.txt")"""
  
  newContents = []
  ignoreLine = False
  with open(fileName, "r") as data:
    contents = data.readlines()

  for line in contents:
    if line.find(STARTMARKER) >= 0:
      ignoreLine = True
    elif line.find(ENDMARKER) >= 0:
      # parse the section name and call insertSection
      sectionName = line.split(ENDMARKER)[1].split(")")[0]
      insertSection(newContents, sectionName)
      ignoreLine = False
    else:
      if not ignoreLine:
        newContents.append(line)

  with open(fileName, "w+") as out:
    for line in newContents:
      out.write(line)
    logInfo("generated %s" % fileName)

# start of main program

parser = argparse.ArgumentParser(description='Foo bar')
parser.add_argument("-d", "--debug", help="increase output verbosity", action="store_true")
parser.add_argument('files', nargs='*')
args = parser.parse_args()

DEBUG = args.debug

if len(args.files) == 0:
  urlBase = "https://raw.githubusercontent.com/opentx/opentx/master/radio/src/lua/"
  args.files = [ urlBase + f for f in ("api_general.cpp", "api_lcd.cpp", "api_model.cpp")]

for fileName in args.files:
  logInfo("Opening %s" % fileName)
  if fileName.startswith("http"):
    inp = urllib2.urlopen(fileName)
  else:
    inp = open(fileName, "r")
  data = inp.read()
  inp.close()
  parseSource(data)

#show gathered data
for m in MODULES.iterkeys():
  summary = ""
  logDebug("Module: %s" % m)
  for f in sorted(MODULES[m]):
    # f = (moduleName, funcName, funcDefinition, description, params, retvals, notices)
    logDebug("Function: %s" % repr(f))
    doc = generateFunctionDoc(f)
    # print(doc)
    docName = "%s/%s.md" % (f[0], f[1])
    mkdir_p(os.path.dirname(docName))
    with open(docName, "w") as out:
      out.write(doc)
      logInfo("generated %s" % docName)
    if f[0] != "general":
      summary += "       * [%s.%s()](%s)\n" % (f[0], f[1], docName)
    else:
      summary += "       * [%s()](%s)\n" % (f[1], docName)
  print("Summary:")
  print(summary)

#now update SUMMARY.MD replacing the outdated sections
replaceSections(SUMMARYFILE)

#now update the timestamp in README.md
replaceSections(READMEFILE)
