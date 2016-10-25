# encoding: utf-8

from __future__ import unicode_literals, print_function

from marrow.script import Script


class NavalFate(object):
	"""Naval Fate
	
	An adaption of a docopt example adapted to click adapted to marrow.script.
	
	For comparison, see: https://github.com/pallets/click/blob/master/examples/naval/naval.py
	"""
	
	class ship(object):
		"""Manage ships."""
		
		def new(self, name):
			"""Create a new ship."""
			print("Created ship", name)
		
		def move(self, ship, x: float, y: float, speed: (int, "Speed in knots.") = 10):
			"""Move SHIP to the new location X, Y."""
			print("Moving ship {} to {},{} with speed {} knots.".format(ship, x, y, speed))
		
		def shoot(self, ship, x: float, y: float):
			"""Make SHIP fire at position X, Y."""
			print("Ship {} fires at {},{}.".format(ship, x, y))
		
	class mine(object):
		"""Manage mines."""
		def set(self, x: float, y: float, drifting=False):
			"""Sets a mine at a specific coordinate."""
			print("Set {} mine at {},{}.".format("drifting" if drifting else "moored", x, y))
		
		def remove(self, x: float, y: float):
			"""Remove a mine at a specific coordinate."""
			print("Removed mine at {},{}.".format(x, y))


if __name__ == '__main__':
	Script.from_object(NavalFate).run()
