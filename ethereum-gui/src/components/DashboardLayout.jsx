import './styles/dashboardlayout.css';
import SideBar from "./SideBar";
import EthereumBlockExplorer from "./EthereumBlockExplorer";

const Layout = ({ children }) => {


    return (
        <section id="dashboardlayout">
            {children}
            <section id='blockchain_dashboard'>
                <SideBar />
                <EthereumBlockExplorer />
            </section>
        </section>
    );
};

export default Layout;


/*
    <main id="root">
        <section id="dashboardlayout">
            {children}
        </section>
    </main>
*/



