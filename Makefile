nautilus_path=`which nautilus`

ifeq ($(strip $(DESTDIR)),)
	INSTALL_DIR = $(HOME)/.local/share/nautilus-python/extensions
else
	INSTALL_DIR = $(DESTDIR)/share/nautilus-python/extensions
endif

.PHONY: install uninstall

install:
	mkdir -p $(INSTALL_DIR)
	cp -a src/nautilus_tmsu.py $(INSTALL_DIR)
	cp -a src/nautilus-tmsu $(INSTALL_DIR)
	@echo "Restarting nautilus"
	@${nautilus_path} -q||true

uninstall:
	rm -rf $(INSTALL_DIR)/nautilus_tmsu.py
	rm -rf $(INSTALL_DIR)/nautilus-tmsu
	@echo "Restarting nautilus"
	@${nautilus_path} -q||true
