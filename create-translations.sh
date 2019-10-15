# Update translation file
cd po; for i in *; do
	cd $i
	msgfmt -o nautilus-templates.mo nautilus-templates.po
	MDIR="../../usr/share/locale/$i/LC_MESSAGES/"
	mkdir -p ${MDIR}
	rm -f ${MDIR}/nautilus-templates.mo
	cp nautilus-templates.mo ${MDIR}
	cd ..
done
cd ..
