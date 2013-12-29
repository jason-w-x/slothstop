all: CPrediction.o main.o
	g++ CPrediction.o main.o -o run -std=c++11

main: main.cpp
	g++ -c main.cpp -std=c++11

CPrediction: CPrediction.cpp CPrediction.h
	g++ -c CPrediction.cpp -std=c++11

clean:
	rm -rf *.o run *~