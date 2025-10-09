.PHONY: install test dash lint

install:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

test:
	python -m unittest discover -s tests -p 'test*.py' -v

dash:
	python dash_app.py

lint:
	python -m compileall meeting_room_booking.py dash_app.py
