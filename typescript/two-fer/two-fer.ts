class TwoFer {
  public static twoFer(name?: string ): string {
    if( name){
	return "One for " + name + ", one for me.";
    }
    return "One for you, one for me."
  }
}

export default TwoFer
