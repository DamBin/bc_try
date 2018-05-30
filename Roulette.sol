pragma solidity ^0.4.18;



contract Roulette{

	mapping (address => uint256) private puntata;
	mapping (address => uint32) private numero;
	address[] public lista_giocatori;
    address public owner;
    uint256 private amount;


	constructor() payable public {
	    owner = msg.sender;
	    amount = msg.value;
	}


    function get_amount() public constant returns(uint256){
        require(owner==msg.sender);
        return amount;
    }

    function transfer_all() public {
        require(owner==msg.sender);
        owner.transfer(amount);
    }
    
	function punta(uint32 num) payable public {
	    address indirizzo = msg.sender;
		require(!address_exists(indirizzo));
		require(num<=5 && num>0);
		numero[indirizzo] = num;
		puntata[indirizzo] = msg.value;
		lista_giocatori.push(indirizzo);
		amount += msg.value;
	}



	function gioca(uint32 num_ex) public {
	    require(owner==msg.sender);
	    require(num_ex<=5 && num_ex>0);
        for (uint256 i=0; i<lista_giocatori.length;i++){
            if (numero[lista_giocatori[i]]==num_ex)
                lista_giocatori[i].transfer(puntata[lista_giocatori[i]]*5);
        }
        delete lista_giocatori;
	}

	

	function address_exists(address indirizzo) private constant returns(bool) {
		for (uint256 i=0; i<lista_giocatori.length;i++){
			if (lista_giocatori[i]==indirizzo)
				return true;
		}
		return false;
	}
}
