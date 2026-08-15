# Settings
VERSION = 2.0.0
TARGET = WaxCheat-$(VERSION).exe
CC = g++
CFLAGS = -Wall -Wextra -std=c++26 -g -Isrc -Ioffsets -Iwinapi
SRC_DIR = src
BUILD_DIR = build

SRC := $(wildcard $(SRC_DIR)/*.cpp)
OBJ := $(SRC:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
DEP := $(OBJ:.o=.d)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(OBJ) -o $(TARGET)
	@echo "Build complete: $(TARGET)"

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

-include $(DEP)

clean:
	rm -rf $(BUILD_DIR) $(TARGET)
	@echo "Cleaned"