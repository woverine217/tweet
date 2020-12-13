import React from "react";
import {
  View,
  TouchableHighlight,
  Text,
  StyleSheet
} from "react-native";

const styles = StyleSheet.create({
  actionsContainer: {
    flex: 1,
    flexDirection: "row",
    justifyContent: "flex-end",
    alignItems: "center",
    padding: 10
  },
  actionButton: {
    padding: 10,
    borderRadius: 6,
    width: 90,
    backgroundColor: "lightblue",
    marginRight: 5,
    marginLeft: 5
  },
  actionButtonDestructive: {
    backgroundColor: "pink"
  },
  actionButtonText: {
    textAlign: "center"
  }
});

const TweetActions = () => {
  return (
    <View style={styles.actionsContainer}>
      <TouchableHighlight
        style={styles.actionButton}
        onPress={() => {
          alert("You could do something with this about-me action!");
        }}
      >
        <Text style={styles.actionButtonText}>Reply</Text>
      </TouchableHighlight>
      <TouchableHighlight
        style={[styles.actionButton, styles.actionButtonDestructive]}
        onPress={() => {
          "do some"
        }}
      ><Text style={styles.actionButtonText}>Upvote</Text>
      </TouchableHighlight>
    </View>
  );
};

export default TweetActions;
