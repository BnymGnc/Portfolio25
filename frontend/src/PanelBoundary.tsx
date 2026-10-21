import {Component,type ReactNode} from 'react';
export default class PanelBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<section className="panel"><p role="alert">Bu bölüm gösterilemedi. Diğer bölümler ve kayıtlarınız korunur.</p><button className="button secondary" onClick={()=>this.setState({failed:false})}>Bölümü yeniden dene</button></section>:this.props.children}
}
