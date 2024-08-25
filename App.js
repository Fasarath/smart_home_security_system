import React, { useState } from 'react';
import { View, Text, Button, FlatList, StyleSheet, TextInput, Alert } from 'react-native';

const API_URL = 'http://192.168.8.101:8000/api';

const App = () => {
  const [name, setName] = useState('');
  const [authenticated, setAuthenticated] = useState(null);
  const [authenticatedName, setAuthenticatedName] = useState(null);
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Function to register a person
  const registerPerson = async () => {
    try {
      const response = await fetch(`${API_URL}/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert('Registration Error', errorData.error || 'Registration failed');
        return;
      }

      const data = await response.json();
      Alert.alert('Registration Result', data.success || 'Registration successful');
    } catch (error) {
      console.error('Registration error:', error);
      Alert.alert('Registration Error', 'An error occurred while registering');
    }
  };

  // Function to authenticate a person
  const authenticate = async () => {
    try {
      const response = await fetch(`${API_URL}/authenticate/`);
      const data = await response.json();
      setAuthenticated(data.authenticated);
      setAuthenticatedName(data.name);
    } catch (error) {
      console.error('Authentication error:', error);
      Alert.alert('Authentication Error', 'An error occurred during authentication');
    }
  };

  // Function to delete a person
  const deletePerson = async () => {
    try {
      const response = await fetch(`${API_URL}/delete/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        Alert.alert('Deletion Error', errorData.error || 'Deletion failed');
        return;
      }

      const data = await response.json();
      Alert.alert('Deletion Result', data.message || 'Deletion successful');
    } catch (error) {
      console.error('Deletion error:', error);
      Alert.alert('Deletion Error', 'An error occurred while deleting');
    }
  };

  // Function to fetch authentication logs
  const fetchLogs = async (resetLogs = false) => {
    try {
      if (resetLogs) {
        setPage(1);
        setLogs([]);
      }

      const response = await fetch(`${API_URL}/logs/?page=${page}&page_size=10`);
      const data = await response.json();
      
      if (data.results.length === 0) {
        setHasMore(false);
        return;
      }

      setLogs(prevLogs => [...prevLogs, ...data.results]);
      setShowLogs(true);
      setPage(prevPage => prevPage + 1);
      setHasMore(data.next !== null);
    } catch (error) {
      console.error('Error fetching logs:', error);
      Alert.alert('Logs Error', 'An error occurred while fetching logs');
    }
  };

  const renderFooter = () => {
    if (!hasMore) return null;
    return (
      <Button 
        title="Load More" 
        onPress={() => fetchLogs()} 
        disabled={!hasMore}
      />
    );
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Enter Name"
        value={name}
        onChangeText={setName}
      />
      <View style={styles.buttonContainer}>
        <Button title="Register" onPress={registerPerson} />
        <Button title="Authenticate" onPress={authenticate} />
        <Button title="Delete" onPress={deletePerson} />
        <Button title="Show Logs" onPress={() => fetchLogs(true)} />
      </View>
      
      {authenticated !== null && (
        <Text style={styles.result}>
          Authentication {authenticated ? 'Successful' : 'Failed'}
          {authenticated && authenticatedName && ` - Welcome, ${authenticatedName}!`}
        </Text>
      )}
      
      {showLogs && (
        <>
          <Text style={styles.header}>Authentication Logs:</Text>
          <FlatList
            data={logs}
            keyExtractor={(item, index) => `${item.id}-${index}`}
            renderItem={({ item }) => (
              <Text style={styles.logItem}>
                {new Date(item.timestamp).toLocaleString()} - 
                {item.authenticated ? 'Success' : 'Failure'}
              </Text>
            )}
            ListFooterComponent={renderFooter}
          />
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  input: {
    borderWidth: 1,
    padding: 10,
    marginBottom: 10,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  result: {
    fontSize: 18,
    marginVertical: 10,
  },
  header: {
    fontSize: 20,
    fontWeight: 'bold',
    marginTop: 20,
    marginBottom: 10,
  },
  logItem: {
    marginBottom: 5,
  },
});

export default App;