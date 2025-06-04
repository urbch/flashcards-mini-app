import { useEffect, useState } from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import { useSwipeable } from 'react-swipeable';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [decks, setDecks] = useState([]);
  const [deckName, setDeckName] = useState('');
  const [showDecks, setShowDecks] = useState(false);
  const [selectedDeck, setSelectedDeck] = useState(null);
  const [cards, setCards] = useState([]);
  const [showCardModal, setShowCardModal] = useState(false);
  const [cardRows, setCardRows] = useState([]);
  const [studyMode, setStudyMode] = useState(false);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState(null);

  const fetchUserInfo = async (telegramId) => {
    try {
      const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/user/${telegramId}/`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Fetched user info:', data);
      return data;
    } catch (error) {
      console.error('Error fetching user info:', error);
      return { id: telegramId, first_name: 'Guest' }; // Запасной вариант
    }
  };

  useEffect(() => {
    TelegramWebApp.ready();
    const initDataRaw = TelegramWebApp.initData;
    const initData = TelegramWebApp.initDataUnsafe;
    console.log('Raw initData:', initDataRaw);
    console.log('Parsed initData:', JSON.stringify(initData, null, 2));
    console.log('Telegram version:', TelegramWebApp.version);
    console.log('Platform:', TelegramWebApp.platform);

    const setUserData = async () => {
      if (initData && initData.user) {
        setUser(initData.user);
        console.log('User set from initData:', initData.user);
      } else {
        console.warn('No user data in initData, falling back to URL parameter');
        const urlParams = new URLSearchParams(window.location.search);
        const telegramIdFromUrl = urlParams.get('telegram_id');
        if (telegramIdFromUrl) {
          const telegramId = parseInt(telegramIdFromUrl);
          const userInfo = await fetchUserInfo(telegramId);
          setUser(userInfo);
          console.log('Set user from fetched info:', userInfo);
        } else {
          console.error('No user data in initData or URL:', initData);
        }
      }
    };

    setUserData();
  }, []);

  useEffect(() => {
    console.log('Decks state updated:', decks);
  }, [decks]);

  const fetchDecks = async () => {
    if (!user || !user.id) {
      console.error('No user ID available for fetching decks');
      return;
    }
    try {
      const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/decks/${user?.id}`, {
        method: "get",
        headers: new Headers({
          "ngrok-skip-browser-warning": "69420",
        }),
      });
      console.log('Status:', response.status);
      const contentType = response.headers.get("content-type");
      console.log('Content-Type:', contentType);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        console.log('Received decks data:', data);
        setDecks(data);
      } else {
        const textData = await response.text();
        console.warn('Expected JSON but got:', textData);
      }
    } catch (error) {
      console.error('Error fetching decks:', error);
    }
  };

  const createDeck = async () => {
    if (!user || !user.id || !deckName || !deckName.trim()) {
      console.error('Cannot create deck: invalid data', { user, deckName });
      return;
    }
    const payload = { telegram_id: user.id, name: deckName.trim() };
    console.log('Sending to /decks/:', payload);
    try {
      const response = await fetch('https://f09b-194-58-154-209.ngrok-free.app/decks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      setDeckName('');
      if (showDecks) {
        await fetchDecks();
      }
    } catch (error) {
      console.error('Error creating deck:', error);
    }
  };

  const handleShowDecks = async () => {
    console.log('Show decks toggled, current showDecks:', showDecks);
    if (!showDecks) {
      await fetchDecks();
    }
    setShowDecks(!showDecks);
    setSelectedDeck(null);
    setCards([]);
    setShowCardModal(false);
    setStudyMode(false);
  };

  const openAddCardsModal = async (deckId) => {
    setSelectedDeck(deckId);
    setShowCardModal(true);
    try {
      const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/cards/${deckId}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Received cards data:', data);
      setCards(data);
      setCardRows(data.map(card => ({ id: card.id, term: card.term, definition: card.definition })));
    } catch (error) {
      console.error('Error fetching cards:', error);
      setCardRows([]);
    }
  };

  const startStudy = async (deckId) => {
    setSelectedDeck(deckId);
    setStudyMode(true);
    try {
      const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/cards/${deckId}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' }
      });
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      const data = await response.json();
      console.log('Received cards data:', data);
      setCards(data);
      setCurrentCardIndex(0);
      setIsFlipped(false);
    } catch (error) {
      console.error('Error fetching cards:', error);
    }
  };

  const addNewCardRow = () => {
    setCardRows([...cardRows, { term: '', definition: '' }]);
  };

  const updateCardRow = (index, field, value) => {
    const updatedRows = [...cardRows];
    updatedRows[index][field] = value;
    setCardRows(updatedRows);
  };

  const removeCardRow = async (index) => {
    const row = cardRows[index];
    if (row.id) {
      try {
        const response = await fetch(`https://f09b-194-58-154-209.ngrok-free.app/cards/${row.id}`, {
          method: 'DELETE',
          headers: { 'ngrok-skip-browser-warning': '69420' }
        });
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
        }
        setCards(cards.filter(c => c.id !== row.id));
      } catch (error) {
        console.error('Error deleting card:', error);
      }
    }
    setCardRows(cardRows.filter((_, i) => i !== index));
  };

  const saveCards = async () => {
    if (!selectedDeck) {
      console.error('No deck selected');
      return;
    }

    const newCards = cardRows.filter(row => !row.id && row.term.trim() && row.definition.trim());
    const updatedCards = cardRows.filter(row => row.id && (row.term.trim() !== cards.find(c => c.id === row.id)?.term || row.definition.trim() !== cards.find(c => c.id === row.id)?.definition));

    try {
      const createPromises = newCards.map(card =>
          fetch('https://f09b-194-58-154-209.ngrok-free.app/cards/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
            body: JSON.stringify({ deck_id: selectedDeck, term: card.term.trim(), definition: card.definition.trim() })
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
            }
            return response.json();
          })
      );

      const updatePromises = updatedCards.map(card =>
          fetch(`https://f09b-194-58-154-209.ngrok-free.app/cards/${card.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
            body: JSON.stringify({ term: card.term.trim(), definition: card.definition.trim() })
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`HTTP error! Status: ${response.status}, ${JSON.stringify(errorData)}`);
            }
            return response.json();
          })
      );

      const [newCardsData, updatedCardsData] = await Promise.all([
        Promise.all(createPromises),
        Promise.all(updatePromises)
      ]);

      setCards([
        ...cards.filter(c => !updatedCards.some(uc => uc.id === c.id)),
        ...newCardsData,
        ...updatedCardsData
      ]);
      setCardRows([]);
      setShowCardModal(false);
    } catch (error) {
      console.error('Error saving cards:', error);
    }
  };

  const closeModal = () => {
    setShowCardModal(false);
    setCardRows([]);
  };

  const handleSwipe = (direction) => {
    if (currentCardIndex < cards.length - 1) {
      setSwipeDirection(direction);
      setTimeout(() => {
        setCurrentCardIndex(currentCardIndex + 1);
        setIsFlipped(false);
        setSwipeDirection(null);
      }, 300); // Длительность анимации
    } else {
      setSwipeDirection(direction);
      setTimeout(() => {
        exitStudy();
      }, 300);
    }
  };

  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => handleSwipe('left'),
    onSwipedRight: () => handleSwipe('right'),
    trackMouse: true, // Для тестирования на десктопе
  });

  const toggleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const exitStudy = () => {
    setStudyMode(false);
    setSelectedDeck(null);
    setCards([]);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
  };

  if (!user) {
    return <p>Не удалось загрузить данные пользователя. Пожалуйста, перезапустите бота или проверьте настройки.</p>;
  }

  if (studyMode && selectedDeck) {
    return (
        <div className="App study">
          <h1>Изучение карточек</h1>
          <p className="card-counter">Карточка {currentCardIndex + 1} из {cards.length}</p>
          {cards.length > 0 ? (
              <div className="study-container" {...swipeHandlers}>
                <div
                    className={`study-card ${isFlipped ? 'flipped' : ''} ${swipeDirection ? `swipe-${swipeDirection}` : ''}`}
                    onClick={toggleFlip}
                >
                  <div className="card-front">
                    <div className="card-content">
                      <p>{cards[currentCardIndex].term}</p>
                    </div>
                  </div>
                  <div className="card-back">
                    <div className="card-content">
                      <p>{cards[currentCardIndex].definition}</p>
                    </div>
                  </div>
                </div>
              </div>
          ) : (
              <p>Добавьте карточки, чтобы начать изучение.</p>
          )
          }
          <p>Свайпните влево, если не запомнили. Вправо — если запомнили.</p>
          <div className="study-buttons">
            <button onClick={exitStudy}>Завершить</button>
          </div>
        </div>
    );
  }

  return (
      <div className="App">
        <h1>Flashcards Mini App</h1>
        <p>Привет!</p>
        <div className="create-deck">
          <input
              type="text"
              value={deckName}
              onChange={(e) => setDeckName(e.target.value)}
              placeholder="Название колоды"
          />
          <button onClick={createDeck}>Создать колоду</button>
        </div>
        <div>
          <button className="toggle-decks-button" onClick={handleShowDecks}>
            {showDecks ? 'Скрыть колоды' : 'Мои колоды'}
          </button>
        </div>
        {showDecks && (
            <div className="decks-container">
              <h2>Ваши колоды:</h2>
              <ul>
                {decks.length > 0 ? (
                    decks.map((deck) => (
                        <li key={deck.id} className="deck-item">
                          <span>{deck.name}</span>
                          <div className="deck-actions">
                            <button className="add-cards-button" onClick={() => openAddCardsModal(deck.id)}>Карточки</button>
                            <button className="study-button" onClick={() => startStudy(deck.id)}>Изучить</button>
                          </div>
                        </li>
                    ))
                ) : (
                    <p>У вас пока нет колод.</p>
                )}
              </ul>
            </div>
        )}
        {showCardModal && selectedDeck && (
            <div className="modal">
              <div className="modal-content">
                <h2>Редактировать карточки</h2>
                <div className="card-form">
                  {cardRows.map((row, index) => (
                      <div key={row.id || `new-${index}`} className="card-row">
                        <input
                            type="text"
                            value={row.term}
                            onChange={(e) => updateCardRow(index, 'term', e.target.value)}
                            placeholder="Термин"
                        />
                        <textarea
                            value={row.definition}
                            onChange={(e) => updateCardRow(index, 'definition', e.target.value)}
                            placeholder="Определение"
                            rows="3"
                        />
                        <button className="remove-row" onClick={() => removeCardRow(index)}>×</button>
                      </div>
                  ))}
                  <button className="add-row" onClick={addNewCardRow}>+</button>
                  <div className="modal-buttons">
                    <button onClick={saveCards}>Сохранить</button>
                    <button onClick={closeModal}>Закрыть</button>
                  </div>
                </div>
              </div>
            </div>
        )}
      </div>
  );
}


export default App;