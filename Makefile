SET:=test

run:
	python2 run.py

regions:
	PYTHONPATH=. python2 scripts/create_region_graph.py $(SET).txt $(SET) --regions-connection next-highest-depth

trees:
	PYTHONPATH=. python2 scripts/create_tree.py $(SET)_graph.gt $(SET)_tree --threshold 32

mongo:
	PYTHONPATH=. python2 scripts/mongo_populate_regions.py $(SET)_regions.pkl $(SET)
	PYTHONPATH=. python2 scripts/mongo_update_elements.py $(SET)_elem_assoc.pkl $(SET)

copy:
	cp $(SET)_graph.gt app/data/graphs/
	cp $(SET)_tree.pkl app/data/trees/

clean:
	rm $(SET)_*
