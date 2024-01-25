# Makefile for LaTeX document with BibTeX bibliography

MAIN = main

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex appendix/appendix.tex background/background.tex conclusion/conclusion.tex evaluation/evaluation.tex introduction/introduction.tex project/project.tex title/title.tex bibs/bibliography.bib
	pdflatex -interaction nonstopmode $(MAIN).tex || true
	bibtex $(MAIN) || true
	pdflatex -interaction nonstopmode $(MAIN).tex || true
	pdflatex -interaction nonstopmode $(MAIN).tex || true

clean:
	rm -f $(MAIN).pdf $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out

.PHONY: all clean
