nautilus_path=`which nautilus`

ifeq ($(strip $(DESTDIR)),)
	INSTALL_DIR = $(HOME)/.local/share/nautilus-python/extensions
else
	INSTALL_DIR = $(DESTDIR)/share/nautilus-python/extensions
endif

.PHONY: copy_files dev_install install link_files uninstall

copy_files:
	mkdir -p $(INSTALL_DIR)
	cp -a src/nautilus_tmsu.py $(INSTALL_DIR)
	cp -a src/nautilus-tmsu $(INSTALL_DIR)

dev_install: link_files restart_nautilus

install: copy_files restart_nautilus

link_files:
	mkdir -p $(INSTALL_DIR)
	ln -sf $(realpath ./src/nautilus_tmsu.py) $(INSTALL_DIR)/nautilus_tmsu.py
	ln -sf $(realpath ./src/nautilus-tmsu) $(INSTALL_DIR)

restart_nautilus:
	@echo "Restarting nautilus"
	@$(nautilus_path) -q||true

uninstall:
	rm -rf $(INSTALL_DIR)/nautilus_tmsu.py
	rm -rf $(INSTALL_DIR)/nautilus-tmsu
	@echo "Restarting nautilus"
	@${nautilus_path} -q||true
