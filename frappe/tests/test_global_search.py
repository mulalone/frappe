# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import unittest
import frappe

from frappe.utils import global_search
from frappe.test_runner import make_test_objects
import frappe.utils

class TestGlobalSearch(unittest.TestCase):
	def setUp(self):
		global_search.setup_global_search_table()
		self.assertTrue('__global_search' in frappe.db.get_tables())
		doctype = "Event"
		global_search.reset()
		from frappe.custom.doctype.property_setter.property_setter import make_property_setter
		make_property_setter(doctype, "subject", "in_global_search", 1, "Int")
		make_property_setter(doctype, "event_type", "in_global_search", 1, "Int")
		make_property_setter(doctype, "roles", "in_global_search", 1, "Int")
		make_property_setter(doctype, "repeat_on", "in_global_search", 0, "Int")

	def tearDown(self):
		frappe.db.sql('delete from `tabProperty Setter` where doc_type="Event"')
		frappe.clear_cache(doctype='Event')
		frappe.db.sql('delete from `tabEvent`')
		frappe.db.sql('delete from `tabEvent Role`')
		frappe.db.sql('delete from __global_search')
		make_test_objects('Event')
		frappe.db.commit()

	def insert_test_events(self):
		frappe.db.sql('delete from tabEvent')
		phrases = ['"The Sixth Extinction II: Amor Fati" is the second episode of the seventh season of the American science fiction.',
		'After Mulder awakens from his coma, he realizes his duty to prevent alien colonization. ',
		'Carter explored themes of extraterrestrial involvement in ancient mass extinctions in this episode, the third in a trilogy.']

		for text in phrases:
			frappe.get_doc(dict(
				doctype='Event',
				subject=text,
				repeat_on='Every Month',
				starts_on=frappe.utils.now_datetime())).insert()

		frappe.db.commit()

	def test_search(self):
		self.insert_test_events()
		results = global_search.search('awakens')
		self.assertTrue('After Mulder awakens from his coma, he realizes his duty to prevent alien colonization. ' in results[0].content)

		results = global_search.search('extraterrestrial')
		self.assertTrue('Carter explored themes of extraterrestrial involvement in ancient mass extinctions in this episode, the third in a trilogy.' in results[0].content)

	def test_update_doc(self):
		self.insert_test_events()
		test_subject = 'testing global search'
		event = frappe.get_doc('Event', frappe.get_all('Event')[0].name)
		event.subject = test_subject
		event.save()
		frappe.db.commit()

		results = global_search.search('testing global search')

		self.assertTrue('testing global search' in results[0].content)

	def test_update_fields(self):
		self.insert_test_events()
		results = global_search.search('Every Month')
		self.assertEquals(len(results), 0)
		doctype = "Event"
		from frappe.custom.doctype.property_setter.property_setter import make_property_setter
		make_property_setter(doctype, "repeat_on", "in_global_search", 1, "Int")
		global_search.rebuild_for_doctype(doctype)
		results = global_search.search('Every Month')
		self.assertEquals(len(results), 3)

	def test_delete_doc(self):
		self.insert_test_events()

		event_name = frappe.get_all('Event')[0].name
		event = frappe.get_doc('Event', event_name)
		test_subject = event.subject
		results = global_search.search(test_subject)
		self.assertEquals(len(results), 1)

		frappe.delete_doc('Event', event_name)

		results = global_search.search(test_subject)
		self.assertEquals(len(results), 0)

	def test_insert_child_table(self):
		frappe.db.sql('delete from tabEvent')
		frappe.db.sql('delete from `tabEvent Role`')
		phrases = ['Hydrus is a small constellation in the deep southern sky. ',
		'It was first depicted on a celestial atlas by Johann Bayer in his 1603 Uranometria. ',
		'The French explorer and astronomer Nicolas Louis de Lacaille charted the brighter stars and gave their Bayer designations in 1756. ',
		'Its name means "male water snake", as opposed to Hydra, a much larger constellation that represents a female water snake. ',
		'It remains below the horizon for most Northern Hemisphere observers.',
		'The brightest star is the 2.8-magnitude Beta Hydri, also the closest reasonably bright star to the south celestial pole. ',
		'Pulsating between magnitude 3.26 and 3.33, Gamma Hydri is a variable red giant some 60 times the diameter of our Sun. ',
		'Lying near it is VW Hydri, one of the brightest dwarf novae in the heavens. ',
		'Four star systems have been found to have exoplanets to date, most notably HD 10180, which could bear up to nine planetary companions.']

		for text in phrases:
			doc = frappe.get_doc({
				'doctype':'Event',
				'subject': text,
				'starts_on': frappe.utils.now_datetime()
			})
			doc.append('roles', dict(role='Administrator'))
			doc.insert()

		frappe.db.commit()
		results = global_search.search('Administrator')
		self.assertEquals(len(results), 9)
