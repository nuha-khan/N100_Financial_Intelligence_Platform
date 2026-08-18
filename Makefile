.PHONY: load validate ratios test report dashboard api clean

load:
	python -m src.etl.loader

validate:
	python -m src.etl.validator

ratios:
	python -m src.analytics.ratio_engine

test:
	pytest -v tests/

report:
	@echo Generating reports...
	python -m src.reports.portfolio_report

dashboard:
	@echo Launching Streamlit dashboard...
	streamlit run src/dashboard/app.py

api:
	@echo Starting FastAPI server...
	python -m src.api.main

clean:
	del /Q outputs\*.csv 2>nul || exit 0

