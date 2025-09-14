#!/bin/bash

echo ' Запуск тестов'

source ./.venv/bin/activate

pytest --cache-clear app/tests.py
