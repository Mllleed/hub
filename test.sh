#!/bin/bash

echo ' Запуск тестов'

source ./.venv/bin/activate

pytest app/tests.py
