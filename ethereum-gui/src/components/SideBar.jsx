import { Link } from 'react-router-dom';
import './styles/sidebar.css';


function SideBar() {
    return (
        <nav id="sidebar">
            <ul>
                <li>SideBar</li> {/*<li><Link to="/">Ethereum Block Explorer</Link></li>*/}
            </ul>
        </nav>
    );
}

export default SideBar;


/*
    <main id="root">
        <section id="dashboardlayout">
            <nav id="navbar">
                <ul>
                    <li>NavBar</li>
                </ul>
            </nav>
            <nav id="sidebar">
                <ul>
                    <li>SideBar</li>
                </ul>
            </nav>
            ...
        </section>
    </main>
*/








