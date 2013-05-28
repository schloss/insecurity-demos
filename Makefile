
all:
	equivs-build infosec-demos
	lintian *.deb
	

clean: 
	rm *.deb
