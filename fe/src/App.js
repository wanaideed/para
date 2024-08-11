import React, { useState, useEffect } from "react"
import Select from 'react-select';
import { Input, Button, Row, Col, Table } from 'reactstrap';

const footerStyle = {
    position: 'fixed',
    bottom: 0,
    width: '100%',
    display: 'flex',
    justifyContent: 'center',
    padding: '20px 0',
    gap: '10px'
};

const options = [
    { value: 'admin', label: 'Admin' },
    { value: 'user', label: 'User' }
];

const Login = () => {

    const [selectedUser, setSelectedUser] = useState(options[0]);
    const [password, setPassword] = useState('111111');
    const [login, setLogin] = useState(false);
    const [main, setMain] = useState(false);
    const [dataPanel, setDataPanel] = useState(false);
    const [settingPanel, setSettingPanel] = useState(false);

    //main
    const [weight, setWeight] = useState();
    const [datetime, setDatetime] = useState();

    // data
    const [data, setData] = useState([]);
    const [from, setFrom] = useState();
    const [to, setTo] = useState();

    // setting
    const [kuning, setKuning] = useState(1.000);
    const [merah, setMerah] = useState(1.000);
    const [hijau, setHijau] = useState('on');
    const [buzzer, setBuzzer] = useState(1.000);

    const handleNavigate = (panel) => {
        setMain(false);
        setSettingPanel(false);
        setDataPanel(false);

        switch (panel) {
            case 'main':
                setMain(true);
                break;
            case 'settings':
                setSettingPanel(true);
                break;
            case 'data':
                setDataPanel(true);
                break;
            default:
                console.error('Unknown panel:', panel);
        }
    }

    const fetchDataSetting = async () => {
        try {
            const response = await fetch('http://localhost:5000/view-data');
            const result = await response.json();

            if (result.status === 'OK') {
                setBuzzer(result.data.buzzer);
                setHijau(result.data.hijau);
                setKuning(result.data.kuning);
                setMerah(result.data.merah);
            } else {
                console.error('Failed to fetch data');
            }
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleSubmitSetting = async () => {
        const formData = new FormData();
        formData.append('merah', merah);
        formData.append('kuning', kuning);
        formData.append('hijau', hijau);
        formData.append('buzzer', buzzer);

        try {
            const response = await fetch('http://localhost:5000/submit', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                console.log('Form data submitted successfully');
                alert('Data berjaya diubah');
            } else {
                console.error('Failed to submit form data');
                alert('Data gagal diubah');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Data gagal diubah');
        }
    };

    const convertDateFormat = (inputDate) => {
        const date = new Date(inputDate);
        const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
        return formattedDate;
    };

    const handleSearchData = async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('from', convertDateFormat(from));
        formData.append('to', convertDateFormat(to));

        try {
            const res = await fetch('http://localhost:5000/search', {
                method: 'POST',
                body: formData,
            });
            const result = await res.json();
            if (result.status === 'OK') {
                setData(result.data);
            } else {
                console.error('Failed to fetch data');
                alert('Failed to fetch data');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to fetch data');
        }
    };

    const handleExportData = async (e) => {
        e.preventDefault();

        const formData = new FormData();
        formData.append('from', convertDateFormat(from));
        formData.append('to', convertDateFormat(to));

        try {
            const res = await fetch('http://localhost:5000/export', {
                method: 'POST',
                body: formData,
            });
            const result = await res.json();
            if (result.status === 'OK') {
                alert('OK!');
            } else {
                console.error('Failed to export data');
                alert('Failed to export data');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to export data');
        }
    };

    useEffect(() => {
        if (settingPanel) {
            fetchDataSetting();
        }
    }, [settingPanel]);

    // long polling main data
    useEffect(() => {
        let eventSource;

        const setupSSE = () => {
            eventSource = new EventSource('http://localhost:5000/poll');

            eventSource.onmessage = (event) => {
                const result = JSON.parse(event.data);
                console.log('Data received:', result);
                const formattedWeight = parseFloat(result).toFixed(3);
                setWeight(`${formattedWeight} Kg`);
                setDatetime(new Date().toLocaleString("en-GB"));
            };

            eventSource.onerror = (error) => {
                console.error('EventSource failed:', error);
                eventSource.close();
            };
        };

        if (main) {
            setupSSE();
        } else {
            if (eventSource) {
                eventSource.close();
            }
        }

        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [main]);

    return (
        <>
            {
                !login && (
                    <div className="mt-5">
                        <h5 style={{ fontWeight: 'bold' }}>Login</h5>
                        <br />
                        <div className="d-flex align-items-center">
                            <label className="pe-3">Username: </label>
                            <Select
                                styles={{ container: (base) => ({ ...base, width: '50%' }) }}
                                value={selectedUser}
                                onChange={setSelectedUser}
                                options={options}
                                menuPlacement="bottom"
                            />
                        </div>
                        <div className="d-flex align-items-center mt-3">
                            <label style={{ paddingRight: '20px' }}>Password: </label>
                            <Input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-50 h-50 mb-0"
                            />
                        </div>
                        <br />
                        <div className="d-flex align-items-center mt-3">
                            <Button color="primary" style={{ width: '100px' }} onClick={() => { handleNavigate('main'); setLogin(true) }}>Login</Button>
                        </div>
                    </div>
                )
            }
            {
                main && login && (
                    <>
                        <div className="mt-5">
                            <h5 style={{ fontWeight: 'bold' }}>Main</h5>
                            <br />
                            <Row>
                                <Col sm="2">
                                    <label>Weight : </label>
                                </Col>
                                <Col sm="5">
                                    <Input type="text" disabled value={weight} />
                                </Col>
                            </Row>
                            <Row>
                                <Col sm="2">
                                    <label>Datetime : </label>
                                </Col>
                                <Col sm="5">
                                    <Input type="text" disabled value={datetime} />
                                </Col>
                            </Row>
                        </div>
                        <div style={footerStyle}>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('settings')}>Setting</Button>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('data')}>Data</Button>
                            <Button color="danger" style={{ width: '100px', alignSelf: 'center' }} onClick={() => { setLogin(false); setMain(false) }}>Logout</Button>
                        </div>
                    </>
                )
            }
            {
                settingPanel && login && (
                    <>
                        <div className="mt-5">
                            <div className="d-flex align-items-center gap-2">
                                <h5 style={{ fontWeight: 'bold' }}>Setting</h5>
                                <Button color="success" style={{ width: '100px', alignSelf: 'center' }} size="sm" onClick={handleSubmitSetting}>Update</Button>
                            </div>
                            <br />
                            <Row>
                                <Col sm="2">
                                    <label>LED Merah : </label>
                                </Col>
                                <Col sm="5">
                                    <div className="d-flex align-items-center">
                                        <Input type="number" step="0.001" value={merah} onChange={(e) => setMerah(e.target.value)} />
                                        <span className="ms-2 pb-3">Kg</span>
                                    </div>
                                </Col>
                            </Row>
                            <Row>
                                <Col sm="2">
                                    <label>LED Kuning : </label>
                                </Col>
                                <Col sm="5">
                                    <div className="d-flex align-items-center">
                                        <Input type="number" value={kuning} onChange={(e) => setKuning(e.target.value)} />
                                        <span className="ms-2 pb-3">saat</span>
                                    </div>
                                </Col>
                            </Row>
                            <Row>
                                <Col sm="2">
                                    <label>LED Hijau : </label>
                                </Col>
                                <Col sm="5">
                                    <div className="d-flex align-items-center">
                                        <Input type="radio" id="led-on" name="led" value="on" checked={hijau === 'on'} onChange={(e) => setHijau(e.target.value)} />
                                        <label htmlFor="led-on" className="ms-2 pb-3">ON</label>
                                        <Input type="radio" id="led-off" name="led" value="off" checked={hijau === 'off'} className="ms-2" onChange={(e) => setHijau(e.target.value)} />
                                        <label htmlFor="led-off" className="ms-2 pb-3">OFF</label>
                                    </div>
                                </Col>
                            </Row>
                            <Row>
                                <Col sm="2">
                                    <label>Buzzer : </label>
                                </Col>
                                <Col sm="5">
                                    <div className="d-flex align-items-center">
                                        <Input type="number" step="0.001" value={buzzer} onChange={(e) => setBuzzer(e.target.value)} />
                                        <span className="ms-2 pb-3">Kg</span>
                                    </div>
                                </Col>
                            </Row>
                        </div>
                        <div style={footerStyle}>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('main')}>Main</Button>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('data')}>Data</Button>
                            <Button color="danger" style={{ width: '100px', alignSelf: 'center' }} onClick={() => { setLogin(false); setMain(false) }}>Logout</Button>
                        </div>
                    </>
                )
            }
            {
                dataPanel && login && (
                    <>
                        <div className="mt-5">
                            <h5 style={{ fontWeight: 'bold' }}>Data</h5>
                            <br />
                            <Row>
                                <Col sm="1">
                                    <label>From : </label>
                                </Col>
                                <Col sm="5">
                                    <Input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} />
                                </Col>
                            </Row>
                            <Row>
                                <Col sm="1">
                                    <label>To : </label>
                                </Col>
                                <Col sm="5">
                                    <Input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} />
                                </Col>
                                <Col sm="3">
                                    <div className="d-flex align-items-center gap-2">
                                        <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} size="sm" onClick={handleSearchData}>Search</Button>
                                        <Button color="success" style={{ width: '100px', alignSelf: 'center' }} size="sm" onClick={handleExportData}>Export</Button>
                                    </div>
                                </Col>
                            </Row>
                            <div style={{ overflowY: 'auto', height: '300px' }}>
                                <Table striped>
                                    <thead>
                                        <tr>
                                            <th>No</th>
                                            <th>Value</th>
                                            <th>Datetime</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.map((todo, index) => (
                                            <tr key={index}>
                                                <td>{index + 1}</td>
                                                <td>{todo.value}</td>
                                                <td>{todo.datetime}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </Table>
                            </div>
                        </div>
                        <div style={footerStyle}>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('settings')}>Setting</Button>
                            <Button color="primary" style={{ width: '100px', alignSelf: 'center' }} onClick={() => handleNavigate('main')}>Main</Button>
                            <Button color="danger" style={{ width: '100px', alignSelf: 'center' }} onClick={() => { setLogin(false); setMain(false) }}>Logout</Button>
                        </div>
                    </>
                )
            }

        </>
    )
};

export default Login;
