
all:
	equivs-build insecurity-demos
	lintian *.deb
	

clean: 
	rm *.deb
