.PHONY: load validate test ratios report dashboard api clean

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

dashboard:
	@echo Launching Streamlit dashboard...

api:
	@echo Starting FastAPI server...

clean:
	del /Q outputs\*.csv 2>nul || exit 0