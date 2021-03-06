from collections import defaultdict
from .annotation_set import AnnotationSet
import re

class _AnnotationSetsDict(defaultdict):
	def __init__(self, doc, logger):
		self.logger = logger
		self.doc = doc

	def __missing__(self, key):
		annotationSet = AnnotationSet(self.doc, name = key, logger = self.logger)
		self[key] = annotationSet
		# self.logger.append(("CREATE_AS", key))
		return annotationSet

class Document(object):
	def __init__(self, logger, text, features, src=None):
		self.logger = logger
		self.annotationSets = _AnnotationSetsDict(self, self.logger)
		self._text = text
		self.src = src
		self.features = features

	entitydefs = dict()
	@staticmethod
	def unescape(s):
		"""Based on source code from python STL"""
		if '&' not in s:
			return s
		def replaceEntities(s):
			s = s.groups()[0]
			try:
				if s[0] == "#":
					s = s[1:]
					if s[0] in ['x','X']:
						c = int(s[1:], 16)
					else:
						c = int(s)
					return unichr(c)
			except ValueError:
				return '&#'+s+';'
			else:
				# Cannot use name2codepoint directly, because HTMLParser supports apos,
				# which is not part of HTML 4
				import html.entities
				if html.entities.entitydefs is None:
					entitydefs = html.entities.entitydefs = {'apos':u"'"}
					for k, v in htmlentitydefs.name2codepoint.iteritems():
						Document.entitydefs[k] = unichr(v)
				try:
					return Document.entitydefs[s]
				except KeyError:
					return '&'+s+';'

		return re.sub(r"&(#?[xX]?(?:[0-9a-fA-F]+|\w{1,8}));", replaceEntities, s)

	@staticmethod
	def load(json, src=None):
		"""Loads the document from a dictionary that results from GATE json,
			returns a document and a change logger"""
		logger = []

		text = json["text"]
		text = Document.unescape(text)

		features = json["documentFeatures"]

		doc = Document(logger, text, features, src)

		if "entities" in json and len(json["entities"]):
			for entity_key, instances in list(json["entities"].items()):
				annotation_set, annotation_name = entity_key.split(":")
				for entity in instances:
					start, end = entity.pop("indices")
					_id = entity.pop("annotationID")

					doc.annotationSets[annotation_set].add(start, end,
						annotation_name, entity, _id)


		doc._text = doc.text

		del logger[:]
		return doc



	@property
	def text(self):
		return self._text

	@text.setter
	def text(self, value):
		raise NotImplementedError("Text cannot be modified in a Python processing resource")

	def size(self):
		return int(len(self.text))

	def __len__(self):
		return self.size()