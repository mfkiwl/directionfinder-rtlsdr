from fox import direction_finder

#main.py
fox_app = direction_finder()

if __name__ == "__main__":
	fox_app.init_gps()
	fox_app.init_bluetooth()
	fox_app.init_rtl()
	fox_app.main()