import React from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Container } from 'reactstrap';
import App from './App';
import './styles.css';


const rootElement = document.getElementById('root');
const root = createRoot(rootElement);

root.render(
        <div style={{ height: '600px', width: '1024px', overflowY: 'hidden'}}>
                <Container>
                        <App />
                </Container>
        </div>
); 