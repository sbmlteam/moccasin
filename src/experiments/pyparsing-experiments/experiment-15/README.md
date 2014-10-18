This fixes an issue where lines with semi colons looked like they were getting jammed together as a single statement.  That problem was partly due to how the results were getting printed.

I also realized that what I thought was line-oriented statement parsing was in fact not happening that way -- it's currently parsing every expression as it comes along to it.  At first I thought this would be a problem, but actually it may not matter.  Let's move on for now and revisit the problem if it turns out to be a real issue.
