SELECT account_id,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '1' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '1' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '1' THEN debit - credit ELSE 0 END)) AS januari_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '2' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '2' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '2' THEN debit - credit ELSE 0 END)) AS februari_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '3' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '3' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '3' THEN debit - credit ELSE 0 END)) AS maret_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '4' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '4' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '4' THEN debit - credit ELSE 0 END)) AS april_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '5' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '5' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '5' THEN debit - credit ELSE 0 END)) AS mei_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '6' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '6' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '6' THEN debit - credit ELSE 0 END)) AS juni_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '7' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '7' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '7' THEN debit - credit ELSE 0 END)) AS juli_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '8' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '8' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '8' THEN debit - credit ELSE 0 END)) AS agustus_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '9' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '9' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '9' THEN debit - credit ELSE 0 END)) AS september_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '10' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '10' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '10' THEN debit - credit ELSE 0 END)) AS oktober_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '11' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '11' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '11' THEN debit - credit ELSE 0 END)) AS november_debit_kredit_balance,
       (SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '12' THEN debit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '12' THEN credit ELSE 0 END) || ' || '||
       SUM(CASE EXTRACT(MONTH FROM create_date) WHEN '12' THEN debit - credit ELSE 0 END)) AS desember_debit_kredit_balance
       
FROM account_move_line
WHERE EXTRACT(YEAR FROM create_date) = 2019
GROUP BY account_id
ORDER BY account_id