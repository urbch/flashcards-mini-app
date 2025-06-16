import { useEffect, useRef, useState, useCallback } from 'react';
import TelegramWebApp from '@twa-dev/sdk';
import { useSwipeable } from 'react-swipeable';
import ConfirmModal from './ConfirmModal';
import Toast from './Toast';
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
  const [correctCount, setCorrectCount] = useState(0);
  const [incorrectCount, setIncorrectCount] = useState(0);
  const [finishedStudy, setFinishedStudy] = useState(false);
  const [isLanguageDeck, setIsLanguageDeck] = useState(false);
  const [sourceLang, setSourceLang] = useState('');
  const [targetLang, setTargetLang] = useState('');
  const [languages, setLanguages] = useState([]);
  const [isLanguageDeckSelected, setIsLanguageDeckSelected] = useState(false);
  const [translatingRows, setTranslatingRows] = useState({});
  const [confirmModal, setConfirmModal] = useState({
    isOpen: false,
    message: '',
    onConfirm: () => {},
  });
  const [toasts, setToasts] = useState([]);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
  const lastTranslatedWords = useRef({});

  const showToast = (message, type = 'info', duration = 3000) => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type, duration }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const fetchUserInfo = useCallback(async (telegramId) => {
    try {
      const response = await fetch(`${API_URL}/user/${telegramId}/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching user info:', error);
      return { id: telegramId, first_name: 'Guest' };
    }
  }, [API_URL]);

  const fetchLanguages = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/languages/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setLanguages(data);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
    console.log('API_URL:', API_URL);
  }, [API_URL]);

  const fetchTranslation = async (word, sourceLang, targetLang, rowIndex) => {
    console.log('Translating:', { word, sourceLang, targetLang, rowIndex });
    if (!word.trim() || !sourceLang || !targetLang) {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
      return '';
    }
    if (lastTranslatedWords.current[rowIndex] === word.trim()) {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
      return cardRows[rowIndex].translation || '';
    }
    setTranslatingRows(prev => ({ ...prev, [rowIndex]: true }));
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const response = await fetch(`${API_URL}/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '69420' },
        body: JSON.stringify({
          q: word.trim(),
          source: sourceLang,
          target: targetLang,
          format: 'text',
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Translation failed: ${response.status} - ${errorData.detail || 'Unknown error'}`);
      }
      const data = await response.json();
      console.log('Translation response:', data);
      if (!data.translatedText) throw new Error('No translated text in response');
      lastTranslatedWords.current[rowIndex] = word.trim();
      return data.translatedText;
    } catch (error) {
      console.error('Error fetching translation:', { word, sourceLang, targetLang, error: error.message });
      return `Ошибка перевода: ${error.message}`;
    } finally {
      setTranslatingRows(prev => ({ ...prev, [rowIndex]: false }));
    }
  };

  useEffect(() => {
    const setUserData = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const testMode = urlParams.get('test_mode') === 'true';
      const telegramIdFromUrl = urlParams.get('telegram_id');

      if (testMode) {
        console.log('Running in test mode with default Telegram ID: 1');
        setUser({ id: 1, first_name: 'Test User' });
        return;
      }

      TelegramWebApp.ready();

      const initData = TelegramWebApp.initDataUnsafe;
      console.log('InitDataUnsafe:', initData);

      if (initData?.user) {
        setUser(initData.user);
      } else if (telegramIdFromUrl) {
        console.log('Using telegram_id from URL:', telegramIdFromUrl);
        const telegramId = parseInt(telegramIdFromUrl);
        const userInfo = await fetchUserInfo(telegramId);
        setUser(userInfo);
      } else {
        showToast('Ошибка загрузки данных Telegram. Пожалуйста, перезапустите бота.', 'error');
      }
    };

    setUserData();
    fetchLanguages();
  }, [fetchUserInfo, fetchLanguages]);

  const handleWordChange = async (index, value, event) => {
    const updatedRows = [...cardRows];
    updatedRows[index] = { ...updatedRows[index], word: value };

    if (!value.trim()) {
      updatedRows[index] = { ...updatedRows[index], translation: '', isManuallyEdited: false };
      lastTranslatedWords.current[index] = '';
      setCardRows(updatedRows);
      return;
    }

    const triggerTranslation = event && (
        event.key === ' ' ||
        event.key === 'Enter' ||
        event.type === 'blur'
    );

    if (triggerTranslation && value.trim().length >= 1 && !updatedRows[index].isManuallyEdited) {
      const deck = decks.find(d => d.id === selectedDeck);
      if (!deck || !deck.source_lang || !deck.target_lang) return;

      const translation = await fetchTranslation(
          value.trim(),
          deck.source_lang,
          deck.target_lang,
          index
      );
      if (translation && !translation.startsWith('Ошибка перевода')) {
        updatedRows[index] = { ...updatedRows[index], translation, isManuallyEdited: false };
        setCardRows(updatedRows);
      }
    } else {
      setCardRows(updatedRows);
    }
  };

  const handleTranslationChange = (index, value) => {
    const updatedRows = [...cardRows];
    updatedRows[index] = { ...updatedRows[index], translation: value, isManuallyEdited: true };
    setCardRows(updatedRows);
  };

  const fetchDecks = async () => {
    if (!user?.id) return;
    try {
      const response = await fetch(`${API_URL}/decks/${user.id}/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setDecks(data);
    } catch (error) {
      console.error('Error fetching decks:', error);
      {/*showToast(`Ошибка загрузки колод: ${error.message}`, 'error'); */}
    }
  };

  const createDeck = async () => {
    if (!user?.id || !deckName.trim()) {
      showToast('Введите название колоды', 'warning');
      return;
    }
    if (isLanguageDeck && (!sourceLang || !targetLang)) {
      showToast('Выберите исходный и целевой языки для языковой колоды', 'warning');
      return;
    }
    const payload = {
      telegram_id: user.id,
      name: deckName.trim(),
      is_language_deck: isLanguageDeck,
      source_lang: isLanguageDeck ? sourceLang : null,
      target_lang: isLanguageDeck ? targetLang : null,
    };
    try {
      const response = await fetch(`${API_URL}/decks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': '69420',
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
      }
      const newDeck = await response.json();
      showToast(`Колода "${newDeck.name}" успешно создана!`, 'success');
      setDeckName('');
      setIsLanguageDeck(false);
      setSourceLang('');
      setTargetLang('');
      setDecks(prev => [...prev, newDeck]);
      if (showDecks) await fetchDecks();
    } catch (error) {
      console.error('Error creating deck:', error);
      showToast(`Ошибка при создании колоды: ${error.message}`, 'error');
    }
  };

  const deleteDeck = async (deckId) => {
    setConfirmModal({
      isOpen: true,
      message: 'Вы уверены, что хотите удалить эту колоду? Все карточки в ней будут удалены.',
      onConfirm: async () => {
        try {
          const response = await fetch(`${API_URL}/decks/${deckId}`, {
            method: 'DELETE',
            headers: { 'ngrok-skip-browser-warning': '69420' },
          });
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
          }
          setDecks((prev) => prev.filter((deck) => deck.id !== deckId));
          if (selectedDeck === deckId) {
            setSelectedDeck(null);
            setCards([]);
            setShowCardModal(false);
            setStudyMode(false);
          }
          showToast('Колода успешно удалена', 'success');
        } catch (error) {
          console.error('Error deleting deck:', error);
          showToast(`Ошибка при удалении колоды: ${error.message}`, 'error');
        } finally {
          setConfirmModal({ isOpen: false, message: '', onConfirm: () => {} });
        }
      },
      onCancel: () => {
        setConfirmModal({ isOpen: false, message: '', onConfirm: () => {} });
      },
    });
  };

  const handleShowDecks = async () => {
    if (!showDecks) await fetchDecks();
    setShowDecks(!showDecks);
    setSelectedDeck(null);
    setCards([]);
    setShowCardModal(false);
    setStudyMode(false);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
  };

  const openAddCardsModal = async (deckId) => {
    setSelectedDeck(deckId);
    setShowCardModal(true);
    try {
      const deckResponse = await fetch(`${API_URL}/decks/${user.id}/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
      const deckData = await deckResponse.json();
      const deck = deckData.find(d => d.id === deckId);
      setIsLanguageDeckSelected(deck.is_language_deck);

      const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
      const response = await fetch(`${API_URL}${endpoint}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setCards(data);
      setCardRows(data.map(card => (
          deck.is_language_deck
              ? { id: card.id, word: card.word, translation: card.translation || '', isManuallyEdited: false }
              : { id: card.id, term: card.term, definition: card.definition }
      )));
    } catch (error) {
      console.error('Error fetching cards:', error);
      setCardRows([]);
    }
  };

  const startStudy = async (deckId) => {
    setSelectedDeck(deckId);
    setStudyMode(true);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
    try {
      const deckResponse = await fetch(`${API_URL}/decks/${user.id}/`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!deckResponse.ok) throw new Error(`HTTP error! Status: ${deckResponse.status}`);
      const deckData = await deckResponse.json();
      const deck = deckData.find(d => d.id === deckId);
      setIsLanguageDeckSelected(deck.is_language_deck);
      const endpoint = deck.is_language_deck ? `/lang_cards/${deckId}` : `/cards/${deckId}`;
      const response = await fetch(`${API_URL}${endpoint}`, {
        headers: { 'ngrok-skip-browser-warning': '69420' },
      });
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      const data = await response.json();
      setCards(data.map(card => (
          deck.is_language_deck
              ? { id: card.id, term: card.word, definition: card.translation }
              : card
      )));
    } catch (error) {
      console.error('Error fetching cards:', error);
      setCards([]);
    }
  };

  const addNewCardRow = () => {
    const newRow = isLanguageDeckSelected
        ? { word: '', translation: '', isManuallyEdited: false }
        : { term: '', definition: '' };
    setCardRows(prev => [...prev, newRow]);
  };

  const updateCardRow = (index, field, value) => {
    const updatedRows = [...cardRows];
    updatedRows[index] = { ...updatedRows[index], [field]: value };
    setCardRows(updatedRows);
  };

  const removeCardRow = async (index) => {
    const row = cardRows[index];
    if (row.id) {
      try {
        const endpoint = isLanguageDeckSelected ? `/lang_cards/${row.id}` : `/cards/${row.id}`;
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'DELETE',
          headers: { 'ngrok-skip-browser-warning': '69420' },
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        setCards(cards.filter(c => c.id !== row.id));
      } catch (error) {
        console.error('Error deleting card:', error);
      }
    }
    setCardRows(cardRows.filter((_, i) => i !== index));
    setTranslatingRows(prev => {
      const newState = { ...prev };
      delete newState[index];
      return newState;
    });
  };

  const saveCards = async () => {
    if (!selectedDeck) return;
    const deck = decks.find(d => d.id === selectedDeck);
    if (!deck) return;

    const invalidRows = cardRows.filter(row => (
        isLanguageDeckSelected
            ? !row.word.trim() || !row.translation?.trim()
            : !row.term.trim() || !row.definition.trim()
    ));
    if (invalidRows.length > 0) {
      showToast(
          'Заполните все поля для новых карточек (слово и перевод или термин и определение)',
          'warning'
      );
      return;
    }

    const newCards = cardRows.filter(row => !row.id);
    const updatedCards = cardRows.filter(row => row.id && (
        isLanguageDeckSelected
            ? row.word.trim() !== cards.find(c => c.id === row.id)?.word || row.translation?.trim() !== cards.find(c => c.id === row.id)?.translation
            : row.term.trim() !== cards.find(c => c.id === row.id)?.term || row.definition.trim() !== cards.find(c => c.id === row.id)?.definition
    ));

    try {
      const endpoint = isLanguageDeckSelected ? '/lang_cards/' : '/cards/';
      const createPromises = newCards.map(card =>
          fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'ngrok-skip-browser-warning': '69420',
            },
            body: JSON.stringify(
                isLanguageDeckSelected
                    ? {
                      deck_id: selectedDeck,
                      word: card.word.trim(),
                      source_lang: deck.source_lang,
                      target_lang: deck.target_lang,
                      translation: card.translation?.trim() || null
                    }
                    : {
                      deck_id: selectedDeck,
                      term: card.term.trim(),
                      definition: card.definition.trim(),
                    }
            ),
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
            }
            return response.json();
          })
      );

      const updatePromises = updatedCards.map(card =>
          fetch(`${API_URL}${isLanguageDeckSelected ? '/lang_cards/' : '/cards/'}${card.id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'ngrok-skip-browser-warning': '69420',
            },
            body: JSON.stringify(
                isLanguageDeckSelected
                    ? { word: card.word.trim(), translation: card.translation?.trim() || '' }
                    : { term: card.term.trim(), definition: card.definition.trim() }
            ),
          }).then(async response => {
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(`Ошибка: ${JSON.stringify(errorData)}`);
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
        ...newCardsData.map(card => (
            isLanguageDeckSelected
                ? { id: card.id, word: card.word, translation: card.translation }
                : card
        )),
        ...updatedCardsData.map(card => (
            isLanguageDeckSelected
                ? { id: card.id, word: card.word, translation: card.translation }
                : card
        )),
      ]);

      setCardRows([]);
      setShowCardModal(false);
      setTranslatingRows({});
      showToast('Карточки успешно сохранены!', 'success');
    } catch (error) {
      console.error('Error saving cards:', error);
      showToast(`Ошибка при сохранении карточек: ${error.message}`, 'error');
    }
  };

  const closeModal = () => {
    setShowCardModal(false);
    setCardRows([]);
    setTranslatingRows({});
  };

  const handleSwipe = (direction) => {
    if (currentCardIndex < cards.length - 1) {
      if (direction === 'right') setCorrectCount(prev => prev + 1);
      else if (direction === 'left') setIncorrectCount(prev => prev + 1);
      setSwipeDirection(direction);
      setTimeout(() => {
        setCurrentCardIndex(prev => prev + 1);
        setIsFlipped(false);
        setSwipeDirection(null);
      }, 300);
    } else {
      if (direction === 'right') setCorrectCount(prev => prev + 1);
      else if (direction === 'left') setIncorrectCount(prev => prev + 1);
      setSwipeDirection(direction);
      setTimeout(() => setFinishedStudy(true), 300);
    }
  };

  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => handleSwipe('left'),
    onSwipedRight: () => handleSwipe('right'),
    trackMouse: true,
  });

  const toggleFlip = () => setIsFlipped(prev => !prev);

  const exitStudy = () => {
    setStudyMode(false);
    setSelectedDeck(null);
    setCards([]);
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setSwipeDirection(null);
    setFinishedStudy(false);
    setCorrectCount(0);
    setIncorrectCount(0);
  };

  if (!user) {
    return <p>Загрузка данных пользователя...</p>;
  }

  if (studyMode && finishedStudy) {
    return (
        <div className="study-results">
          <h2>Результаты изучения</h2>
          <div className="results-stats">
            <div className="stat-card correct-stat">
              <span className="stat-value">{correctCount}</span>
              <span className="stat-label">Правильно</span>
            </div>
            <div className="stat-card incorrect-stat">
              <span className="stat-value">{incorrectCount}</span>
              <span className="stat-label">Неправильно</span>
            </div>
            <div className="stat-card total-stat">
              <span className="stat-value">{cards.length}</span>
              <span className="stat-label">Всего</span>
            </div>
          </div>
          <div className="results-progress">
            <div className="progress-bar">
              <div
                  className="progress-fill"
                  style={{ width: `${(correctCount / cards.length) * 100}%` }}
              ></div>
            </div>
            <span className="progress-percent">
            {Math.round((correctCount / cards.length) * 100)}% выучено
          </span>
          </div>
          <button onClick={exitStudy} className="primary-button">
            Вернуться к колодам
          </button>
        </div>
    );
  }

  if (studyMode && !finishedStudy) {
    return (
        <div className="App study">
          <h1>Изучение карточек</h1>
          <p className="card-counter">{currentCardIndex + 1} из {cards.length}</p>
          {cards.length > 0 ? (
              <div className="study-container" {...swipeHandlers}>
                <div
                    className={`
                study-card
                ${isFlipped ? 'flipped' : ''}
                ${swipeDirection ? `swipe-${swipeDirection}` : ''}
              `}
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
          )}
          <p>Свайп влево — не запомнил, вправо — запомнил.</p>
          <div className="study-buttons">
            <button onClick={exitStudy}>Завершить</button>
          </div>
        </div>
    );
  }

  return (
      <div className="App">
        <header className="app-header">
          <h1 className="app-title">FlashCards</h1>
        </header>
        <div className="main-container">
          <div className="section-container">
            <h2 className="section-title">Создать новую колоду</h2>
            <div className="deck-creation-card">
              <div className="form-group">
                <input
                    type="text"
                    value={deckName}
                    onChange={(e) => setDeckName(e.target.value)}
                    placeholder="Введите название колоды"
                    className="form-input deck-name-input"
                />
              </div>
              <div className="deck-type-selector">
                <label className="checkbox-label large">
                  <input
                      type="checkbox"
                      checked={isLanguageDeck}
                      onChange={(e) => setIsLanguageDeck(e.target.checked)}
                      className="checkbox-input"
                  />
                  <span className="checkbox-custom"></span>
                  <span className="checkbox-text">Языковая колода</span>
                </label>
              </div>
              {isLanguageDeck && (
                  <div className="language-selectors">
                    <div className="form-group">
                      <select
                          value={sourceLang}
                          onChange={(e) => setSourceLang(e.target.value)}
                          className="form-select language-select"
                      >
                        <option value="">Выберите исходный язык</option>
                        {languages.map(lang => (
                            <option key={lang.code} value={lang.code}>{lang.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <select
                          value={targetLang}
                          onChange={(e) => setTargetLang(e.target.value)}
                          className="form-select language-select"
                      >
                        <option value="">Выберите целевой язык</option>
                        {languages.map(lang => (
                            <option key={lang.code} value={lang.code}>{lang.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
              )}
              <button
                  onClick={createDeck}
                  className="primary-button create-button large"
              >
                Создать колоду
              </button>
            </div>
          </div>
          <div className="section-container decks-section">
            <div className="section-header">
              <h2 className="section-title">Мои колоды</h2>
              <button
                  onClick={handleShowDecks}
                  className={`toggle-button large ${showDecks ? 'active' : ''}`}
                  aria-expanded={showDecks}
              >
                {showDecks ? (
                    <>
                      <span className="icon">▼</span> Скрыть
                    </>
                ) : (
                    <>
                      <span className="icon">►</span> Показать
                    </>
                )}
              </button>
            </div>
            {showDecks && (
                <div className="decks-container">
                  {decks.length > 0 ? (
                      <div className="decks-grid">
                        {decks.map((deck) => (
                            <div key={deck.id} className="deck-card">
                              <div className="deck-info">
                                <h3 className="deck-name">
                                  {deck.name}
                                  {deck.is_language_deck && <span className="language-badge">🌐</span>}
                                </h3>
                                {deck.is_language_deck && (
                                    <div className="deck-languages">
                            <span className="language-pair">
                              {languages.find(l => l.code === deck.source_lang)?.name} →
                              {languages.find(l => l.code === deck.target_lang)?.name}
                            </span>
                                    </div>
                                )}
                              </div>
                              <div className="deck-actions">
                                <button
                                    onClick={() => openAddCardsModal(deck.id)}
                                    className="action-button edit-button"
                                    aria-label="Редактировать карточки"
                                >
                                  <span className="button-icon">Карточки</span>
                                </button>
                                <button
                                    onClick={() => startStudy(deck.id)}
                                    className="action-button study-button"
                                    aria-label="Учить карточки"
                                >
                                  <span className="button-icon">Изучение</span>
                                </button>
                                <button
                                    onClick={() => deleteDeck(deck.id)}
                                    className="action-button delete-button"
                                    aria-label="Удалить колоду"
                                >
                                  <span className="button-icon">🗑️</span>
                                </button>
                              </div>
                            </div>
                        ))}
                      </div>
                  ) : (
                      <div className="empty-state">
                        <p>У вас пока нет колод. Создайте первую!</p>
                      </div>
                  )}
                </div>
            )}
          </div>
        </div>
        {showCardModal && selectedDeck && (
            <div className="modal">
              <div className="modal-content">
                <h2>Редактировать карточки</h2>
                <div className="card-form">
                  {cardRows.map((row, index) => (
                      <div key={row.id || `new-${index}`} className="card-row">
                        {isLanguageDeckSelected ? (
                            <>
                              <input
                                  type="text"
                                  value={row.word}
                                  onChange={(e) => handleWordChange(index, e.target.value, e)}
                                  onKeyDown={(e) => handleWordChange(index, row.word, e)}
                                  onBlur={(e) => handleWordChange(index, row.word, e)}
                                  placeholder="Слово"
                              />
                              <div className="translation-container">
                                <input
                                    type="text"
                                    value={translatingRows[index] ? row.translation || '' : (row.translation || '')}
                                    onChange={(e) => handleTranslationChange(index, e.target.value)}
                                    placeholder={translatingRows[index] ? 'Перевод...' : 'Перевод'}
                                    disabled={translatingRows[index]}
                                />
                                {translatingRows[index] && <span className="loading">...</span>}
                              </div>
                            </>
                        ) : (
                            <>
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
                            </>
                        )}
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
        <ConfirmModal
            isOpen={confirmModal.isOpen}
            message={confirmModal.message}
            onConfirm={confirmModal.onConfirm}
            onCancel={confirmModal.onCancel}
        />
        <div className="toast-container">
          {toasts.map((toast) => (
              <Toast
                  key={toast.id}
                  id={toast.id}
                  message={toast.message}
                  type={toast.type}
                  duration={toast.duration}
                  onClose={removeToast}
              />
          ))}
        </div>
      </div>
  );
}

export default App;
