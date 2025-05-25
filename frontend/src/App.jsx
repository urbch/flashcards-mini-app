import { useEffect, useState } from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [decks, setDecks] = useState([]);
  const [deckName, setDeckName] = useState('');

  useEffect(() => {
    TelegramWebApp.ready();
    const telegramUser = TelegramWebApp.initDataUnsafe.user;
    console.log('Telegram user:', telegramUser); // Отладка
    if (telegramUser && telegramUser.id) {
      setUser(telegramUser);
      fetchDecks(); // Вызываем сразу
    } else {
      console.error('Failed to get Telegram user data');
    }
  }, []);

  const fetchDecks = async () => {
    if (user && user.id) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/decks/${user.id}`);
        if (!response.ok) {
          const errorData = await response.json();
          console.error('Error response:', errorData);
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        setDecks(data);
      } catch (error) {
        console.error('Error fetching decks:', error);
      }
    } else {
      console.log('No user ID available for fetching decks');
    }
  };

  const createDeck = async () => {
    if (user && user.id && deckName && deckName.trim()) {
      const payload = { telegram_id: user.id, name: deckName.trim() };
      console.log('Sending to /decks/:', payload); // Отладка
      try {
        const response = await fetch('http://127.0.0.1:8000/decks/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const errorData = await response.json();
          console.error('Error response:', errorData);
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        await fetchDecks(); // Обновляем список колод
        setDeckName('');
      } catch (error) {
        console.error('Error creating deck:', error);
      }
    } else {
      console.error('Cannot create deck: invalid data', { user, deckName });
    }
  };

  return (
    <div className="App">
      <h1>Flashcards Mini App</h1>
      {user ? <p>Привет, {user.first_name}!</p> : <p>Загрузка...</p>}
      <div>
        <input
          type="text"
          value={deckName}
          onChange={(e) => setDeckName(e.target.value)}
          placeholder="Название колоды"
        />
        <button onClick={createDeck}>Создать колоду</button>
      </div>
      <h2>Ваши колоды:</h2>
      <ul>
        {decks.map((deck) => (
          <li key={deck.id}>{deck.name}</li>
        ))}
      </ul>
    </div>
  );
}

export default App;