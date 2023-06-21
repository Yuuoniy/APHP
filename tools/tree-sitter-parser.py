#!/usr/bin/env python

from tree_sitter import Language, Parser
from xml.dom import minidom
import os
import argparse
import yaml

script_dir = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
rules_file = os.path.abspath(os.path.dirname(os.path.realpath(__file__))) + "/rules.yml"

EMPTY_CONFIG = { 'flattened': [], 'aliased': {}, 'ignored': []}
with open(rules_file, "r") as stream:
  TREE_REWRITE_RULES = yaml.safe_load(stream)

Language.build_library(
  script_dir + '/build/languages.so',
  [
    script_dir + '/tree-sitter-c',
    # script_dir + '/tree-sitter-java',
    # script_dir + '/tree-sitter-javascript',
    # script_dir + '/tree-sitter-r',
    # script_dir + '/tree-sitter-ocaml/ocaml',
    # script_dir + '/tree-sitter-php',
    # script_dir + '/tree-sitter-python',
    # script_dir + '/tree-sitter-ruby',
    # script_dir + '/tree-sitter-typescript/typescript'
  ]
)

PARSERS = {
  "c": Language(script_dir + '/build/languages.so', 'c'),
  # "java": Language(script_dir + '/build/languages.so', 'java'),
  # "javascript": Language(script_dir + '/build/languages.so', 'javascript'),
  # "ocaml": Language(script_dir + '/build/languages.so', 'ocaml'),
  # "php": Language(script_dir + '/build/languages.so', 'php'),
  # "python": Language(script_dir + '/build/languages.so', 'python'),
  # "r": Language(script_dir + '/build/languages.so', 'r'),
  # "ruby": Language(script_dir + '/build/languages.so', 'ruby'),
  # "typescript": Language(script_dir + '/build/languages.so', 'typescript'),
}

positions = [0]

doc = minidom.Document()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="path to the file to parse")
parser.add_argument("language", help="language of to the file to parse")
parser.add_argument("--raw", action="store_true", help="deactivate the rewrite rules")
args = parser.parse_args()

def main(file, language):
  parser = Parser()
  parser.set_language(PARSERS[language])
  config = retrieveConfig(language)
  tree = parser.parse(bytes(readFile(file), "utf8"))

  xmlRoot = toXmlNode(tree.root_node, config)
  doc.appendChild(xmlRoot)
  process(tree.root_node, xmlRoot, config)
  xml = doc.toprettyxml()
  print(xml)

def process(node, xmlNode, config):
  if not node.type in config['flattened']:
    for child in node.children:
      if not child.type in config['ignored']:
        xmlChildNode = toXmlNode(child, config)
        xmlNode.appendChild(xmlChildNode)
        process(child, xmlChildNode, config)

def retrieveConfig(language):
  return TREE_REWRITE_RULES[language] if not args.raw and language in TREE_REWRITE_RULES else EMPTY_CONFIG

def toXmlNode(node, config):
  xmlNode = doc.createElement('tree')
  type = config['aliased'][node.type] if node.type in config['aliased'] else node.type
  xmlNode.setAttribute("type", type)
  startPos = positions[node.start_point[0]] + node.start_point[1]
  endPos = positions[node.end_point[0]] + node.end_point[1]
  length = endPos - startPos
  xmlNode.setAttribute("pos", str(startPos))
  xmlNode.setAttribute("length", str(length))
  if node.child_count == 0 or node.type in config['flattened']:
    xmlNode.setAttribute("label", node.text.decode('utf8'))
  return xmlNode

def readFile(file):
  with open(file, 'r') as file:
    data = file.read()
  index = 0
  for chr in data:
    index += 1
    if chr == '\n':
      positions.append(index)
  return data

main(args.file, args.language)